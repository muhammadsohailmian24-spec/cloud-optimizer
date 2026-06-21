from __future__ import annotations

import socket
import time

import psutil

from app.models import CloudResource, CostRecord, ResourceMetric, SystemLog


LOCAL_RESOURCE_NAME = "local-host-server"
DEFAULT_LOCAL_HOURLY_COST = 0.02


def ensure_local_resource(db) -> CloudResource:
    resource = db.query(CloudResource).filter(CloudResource.name == LOCAL_RESOURCE_NAME).first()
    if resource:
        return resource

    hostname = socket.gethostname()
    resource = CloudResource(
        name=LOCAL_RESOURCE_NAME,
        provider="Local",
        resource_type="Host Server",
        instance_size=hostname,
        region="local",
        hourly_cost=DEFAULT_LOCAL_HOURLY_COST,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    db.add(SystemLog(level="INFO", message=f"Created live monitored resource for host {hostname}."))
    db.commit()
    return resource


def collect_live_metric(db) -> ResourceMetric:
    resource = ensure_local_resource(db)

    net_before = psutil.net_io_counters()
    cpu_percent = psutil.cpu_percent(interval=1)
    net_after = psutil.net_io_counters()

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    network_in_mb = max((net_after.bytes_recv - net_before.bytes_recv) / (1024 * 1024), 0)
    network_out_mb = max((net_after.bytes_sent - net_before.bytes_sent) / (1024 * 1024), 0)

    start = time.perf_counter()
    time.sleep(0.01)
    response_time_ms = (time.perf_counter() - start) * 1000

    metric = ResourceMetric(
        resource_id=resource.id,
        cpu_percent=round(cpu_percent, 2),
        memory_percent=round(memory.percent, 2),
        disk_percent=round(disk.percent, 2),
        network_in_mb=round(network_in_mb, 4),
        network_out_mb=round(network_out_mb, 4),
        response_time_ms=round(response_time_ms, 2),
    )
    db.add(metric)
    db.add(CostRecord(resource_id=resource.id, estimated_cost=resource.hourly_cost))
    db.commit()
    db.refresh(metric)
    return metric

