from types import SimpleNamespace

from app.services.recommendations import build_recommendations


def metric(cpu, memory, disk=40, net_in=1, net_out=1):
    return SimpleNamespace(
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        network_in_mb=net_in,
        network_out_mb=net_out,
    )


def test_underutilised_resource_gets_rightsizing_recommendation():
    resource = SimpleNamespace(name="idle-vm", hourly_cost=0.05)
    metrics = [metric(5, 25) for _ in range(12)]

    recommendations = build_recommendations(resource, metrics)

    assert any(item["category"] == "rightsizing" for item in recommendations)
    assert sum(item["estimated_monthly_saving"] for item in recommendations) > 0


def test_busy_resource_gets_performance_recommendation():
    resource = SimpleNamespace(name="busy-vm", hourly_cost=0.05)
    metrics = [metric(86, 88, net_in=20, net_out=16) for _ in range(12)]

    recommendations = build_recommendations(resource, metrics)

    assert any(item["category"] == "performance" for item in recommendations)

