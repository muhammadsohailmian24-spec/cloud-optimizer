from app.database import SessionLocal, init_db
from app.services.live_metrics import collect_live_metric, ensure_local_resource


def test_live_resource_can_be_created():
    init_db()
    with SessionLocal() as db:
        resource = ensure_local_resource(db)
        resource_name = resource.name
        provider = resource.provider

    assert resource_name == "local-host-server"
    assert provider == "Local"


def test_live_metric_can_be_collected():
    init_db()
    with SessionLocal() as db:
        metric = collect_live_metric(db)

    assert metric.cpu_percent >= 0
    assert metric.memory_percent >= 0
    assert metric.disk_percent >= 0
