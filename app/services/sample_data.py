from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.auth import hash_password
from app.config import settings
from app.models import CloudResource, CostRecord, ResourceMetric, User


def ensure_admin(db):
    user = db.query(User).filter(User.username == settings.admin_username).first()
    if user:
        return user

    user = User(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
        is_admin=True,
    )
    db.add(user)
    db.commit()
    return user


def seed_demo_data(db):
    ensure_admin(db)
    if db.query(CloudResource).count() > 0:
        return

    resources = [
        CloudResource(name="web-api-prod", provider="AWS", resource_type="EC2", instance_size="t3.medium", hourly_cost=0.0416),
        CloudResource(name="worker-low-traffic", provider="AWS", resource_type="EC2", instance_size="t3.small", hourly_cost=0.0208),
        CloudResource(name="database-main", provider="Azure", resource_type="VM", instance_size="B2s", hourly_cost=0.0464),
    ]
    db.add_all(resources)
    db.commit()

    now = datetime.utcnow()
    for resource in resources:
        for hour in range(72, 0, -1):
            timestamp = now - timedelta(hours=hour)
            if "low-traffic" in resource.name:
                cpu = random.uniform(2, 11)
                memory = random.uniform(20, 34)
                network = random.uniform(0.2, 2.5)
            elif "database" in resource.name:
                cpu = random.uniform(45, 88)
                memory = random.uniform(62, 92)
                network = random.uniform(8, 25)
            else:
                cpu = random.uniform(20, 65)
                memory = random.uniform(40, 75)
                network = random.uniform(5, 18)

            if hour in (8, 31) and resource.name == "database-main":
                cpu = random.uniform(92, 98)
                memory = random.uniform(90, 97)

            metric = ResourceMetric(
                resource_id=resource.id,
                timestamp=timestamp,
                cpu_percent=round(cpu, 2),
                memory_percent=round(memory, 2),
                disk_percent=round(random.uniform(35, 86), 2),
                network_in_mb=round(network, 2),
                network_out_mb=round(network * random.uniform(0.5, 1.5), 2),
                response_time_ms=round(random.uniform(80, 420), 2),
            )
            cost = CostRecord(
                resource_id=resource.id,
                timestamp=timestamp,
                estimated_cost=round(resource.hourly_cost * random.uniform(0.95, 1.15), 4),
            )
            db.add(metric)
            db.add(cost)

    db.commit()

