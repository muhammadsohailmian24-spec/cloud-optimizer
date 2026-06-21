import asyncio
from datetime import datetime
from statistics import mean

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.config import settings
from app.database import SessionLocal, get_db, init_db
from app.models import AiPrediction, CloudResource, CostRecord, Recommendation, ResourceMetric, SystemLog, User
from app.services.ml import detect_anomalies, predict_daily_cost
from app.services.live_metrics import collect_live_metric, ensure_local_resource
from app.services.recommendations import build_recommendations
from app.services.sample_data import ensure_admin, seed_demo_data


app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

REQUEST_COUNT = Counter("cloud_optimizer_requests_total", "Total application requests")
RESOURCE_COUNT = Gauge("cloud_optimizer_resources_total", "Total monitored cloud resources")
OPEN_RECOMMENDATIONS = Gauge("cloud_optimizer_open_recommendations_total", "Open optimization recommendations")
LIVE_CPU = Gauge("cloud_optimizer_live_cpu_percent", "Latest live CPU usage percent")
LIVE_MEMORY = Gauge("cloud_optimizer_live_memory_percent", "Latest live memory usage percent")
LIVE_DISK = Gauge("cloud_optimizer_live_disk_percent", "Latest live disk usage percent")


async def live_collection_loop():
    while True:
        try:
            with SessionLocal() as db:
                metric = collect_live_metric(db)
                LIVE_CPU.set(metric.cpu_percent)
                LIVE_MEMORY.set(metric.memory_percent)
                LIVE_DISK.set(metric.disk_percent)
        except Exception:
            pass
        await asyncio.sleep(60)


@app.middleware("http")
async def count_requests(request: Request, call_next):
    REQUEST_COUNT.inc()
    return await call_next(request)


@app.on_event("startup")
def startup():
    init_db()
    with SessionLocal() as db:
        ensure_admin(db)
        ensure_local_resource(db)
        metric = collect_live_metric(db)
        LIVE_CPU.set(metric.cpu_percent)
        LIVE_MEMORY.set(metric.memory_percent)
        LIVE_DISK.set(metric.disk_percent)
    asyncio.create_task(live_collection_loop())


def is_logged_in(request: Request) -> bool:
    return request.cookies.get("cloud_optimizer_session") == "admin"


def login_required(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    return None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if is_logged_in(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password."})

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie("cloud_optimizer_session", "admin", httponly=True, samesite="lax")
    db.add(SystemLog(level="INFO", message=f"User {username} logged in."))
    db.commit()
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("cloud_optimizer_session")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    redirect = login_required(request)
    if redirect:
        return redirect

    resources = db.query(CloudResource).all()
    latest_metrics = []
    total_cost = 0.0
    for resource in resources:
        metric = (
            db.query(ResourceMetric)
            .filter(ResourceMetric.resource_id == resource.id)
            .order_by(ResourceMetric.timestamp.desc())
            .first()
        )
        total_cost += resource.hourly_cost * 24 * 30
        latest_metrics.append({"resource": resource, "metric": metric})

    recommendations = db.query(Recommendation).order_by(Recommendation.timestamp.desc()).limit(10).all()
    RESOURCE_COUNT.set(len(resources))
    OPEN_RECOMMENDATIONS.set(db.query(Recommendation).filter(Recommendation.status == "open").count())

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "resources": resources,
            "latest_metrics": latest_metrics,
            "recommendations": recommendations,
            "total_monthly_cost": round(total_cost, 2),
        },
    )


@app.get("/resources/{resource_id}", response_class=HTMLResponse)
def resource_detail(resource_id: int, request: Request, db: Session = Depends(get_db)):
    redirect = login_required(request)
    if redirect:
        return redirect

    resource = db.get(CloudResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    metrics = (
        db.query(ResourceMetric)
        .filter(ResourceMetric.resource_id == resource_id)
        .order_by(ResourceMetric.timestamp.desc())
        .limit(48)
        .all()
    )
    metrics = list(reversed(metrics))
    costs = (
        db.query(CostRecord)
        .filter(CostRecord.resource_id == resource_id)
        .order_by(CostRecord.timestamp.desc())
        .limit(48)
        .all()
    )
    prediction = predict_daily_cost(list(reversed(costs)))
    return templates.TemplateResponse(
        "resource_detail.html",
        {
            "request": request,
            "resource": resource,
            "metrics": metrics,
            "metric_labels": [metric.timestamp.strftime("%m-%d %H:%M") for metric in metrics],
            "prediction": prediction,
        },
    )


@app.post("/api/metrics")
def create_metric(
    resource_id: int = Form(...),
    cpu_percent: float = Form(...),
    memory_percent: float = Form(...),
    disk_percent: float = Form(...),
    network_in_mb: float = Form(...),
    network_out_mb: float = Form(...),
    response_time_ms: float = Form(120),
    db: Session = Depends(get_db),
):
    metric = ResourceMetric(
        resource_id=resource_id,
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_percent=disk_percent,
        network_in_mb=network_in_mb,
        network_out_mb=network_out_mb,
        response_time_ms=response_time_ms,
    )
    db.add(metric)
    resource = db.get(CloudResource, resource_id)
    if resource:
        db.add(CostRecord(resource_id=resource_id, estimated_cost=resource.hourly_cost))
    db.commit()
    return {"status": "stored", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/analyse")
def analyse(db: Session = Depends(get_db)):
    db.query(Recommendation).delete()
    db.query(AiPrediction).delete()

    resources = db.query(CloudResource).all()
    results = []
    for resource in resources:
        metrics = (
            db.query(ResourceMetric)
            .filter(ResourceMetric.resource_id == resource.id)
            .order_by(ResourceMetric.timestamp.desc())
            .limit(72)
            .all()
        )
        metrics = list(reversed(metrics))
        anomaly_indexes = detect_anomalies(metrics)
        recommendations = build_recommendations(resource, metrics, len(anomaly_indexes))

        cost_records = (
            db.query(CostRecord)
            .filter(CostRecord.resource_id == resource.id)
            .order_by(CostRecord.timestamp.desc())
            .limit(72)
            .all()
        )
        prediction = predict_daily_cost(list(reversed(cost_records)))
        db.add(
            AiPrediction(
                resource_id=resource.id,
                prediction_type="daily_cost",
                predicted_value=prediction.predicted_daily_cost,
                confidence=prediction.confidence,
                details=prediction.details,
            )
        )

        for item in recommendations:
            db.add(Recommendation(resource_id=resource.id, **item))

        results.append(
            {
                "resource": resource.name,
                "anomalies": len(anomaly_indexes),
                "recommendations": len(recommendations),
                "predicted_daily_cost": prediction.predicted_daily_cost,
            }
        )

    db.add(SystemLog(level="INFO", message="AI analysis completed."))
    db.commit()
    return {"status": "analysed", "results": results}


@app.post("/analyse")
def analyse_from_dashboard(db: Session = Depends(get_db)):
    analyse(db)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/api/collect-live")
def collect_live(db: Session = Depends(get_db)):
    metric = collect_live_metric(db)
    LIVE_CPU.set(metric.cpu_percent)
    LIVE_MEMORY.set(metric.memory_percent)
    LIVE_DISK.set(metric.disk_percent)
    return {
        "status": "collected",
        "resource_id": metric.resource_id,
        "cpu_percent": metric.cpu_percent,
        "memory_percent": metric.memory_percent,
        "disk_percent": metric.disk_percent,
        "network_in_mb": metric.network_in_mb,
        "network_out_mb": metric.network_out_mb,
        "timestamp": metric.timestamp.isoformat(),
    }


@app.post("/collect-live")
def collect_live_from_dashboard(db: Session = Depends(get_db)):
    collect_live(db)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/api/seed-demo")
def seed_demo(db: Session = Depends(get_db)):
    seed_demo_data(db)
    return {"status": "demo data ready"}


@app.post("/seed-demo")
def seed_demo_from_dashboard(db: Session = Depends(get_db)):
    seed_demo_data(db)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    metrics = db.query(ResourceMetric).all()
    avg_cpu = round(mean([metric.cpu_percent for metric in metrics]), 2) if metrics else 0
    avg_memory = round(mean([metric.memory_percent for metric in metrics]), 2) if metrics else 0
    monthly_cost = sum(resource.hourly_cost * 24 * 30 for resource in db.query(CloudResource).all())
    savings = sum(item.estimated_monthly_saving for item in db.query(Recommendation).all())
    return {
        "resources": db.query(CloudResource).count(),
        "metrics": len(metrics),
        "average_cpu": avg_cpu,
        "average_memory": avg_memory,
        "estimated_monthly_cost": round(monthly_cost, 2),
        "estimated_monthly_saving": round(savings, 2),
    }


@app.get("/metrics")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
