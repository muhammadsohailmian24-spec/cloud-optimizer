from __future__ import annotations

from statistics import mean


def build_recommendations(resource, metrics, anomaly_count: int = 0) -> list[dict]:
    if not metrics:
        return []

    avg_cpu = mean(metric.cpu_percent for metric in metrics)
    avg_memory = mean(metric.memory_percent for metric in metrics)
    avg_disk = mean(metric.disk_percent for metric in metrics)
    avg_network = mean(metric.network_in_mb + metric.network_out_mb for metric in metrics)

    monthly_cost = resource.hourly_cost * 24 * 30
    recommendations = []

    if avg_cpu < 10 and avg_memory < 35:
        recommendations.append(
            {
                "severity": "high",
                "category": "rightsizing",
                "message": f"{resource.name} appears underutilised. Average CPU is {avg_cpu:.1f}% and memory is {avg_memory:.1f}%. Consider downsizing or scheduling shutdown periods.",
                "estimated_monthly_saving": round(monthly_cost * 0.35, 2),
            }
        )

    if avg_cpu > 80 or avg_memory > 85:
        recommendations.append(
            {
                "severity": "high",
                "category": "performance",
                "message": f"{resource.name} is close to saturation. Average CPU is {avg_cpu:.1f}% and memory is {avg_memory:.1f}%. Consider scaling up or enabling auto-scaling.",
                "estimated_monthly_saving": 0.0,
            }
        )

    if avg_disk > 80:
        recommendations.append(
            {
                "severity": "medium",
                "category": "storage",
                "message": f"{resource.name} has high disk usage at {avg_disk:.1f}%. Consider cleanup, archival storage or increasing disk capacity.",
                "estimated_monthly_saving": 0.0,
            }
        )

    if avg_network < 5 and monthly_cost > 5:
        recommendations.append(
            {
                "severity": "medium",
                "category": "cost",
                "message": f"{resource.name} has low traffic but still costs about ${monthly_cost:.2f} per month. Review whether the resource is needed continuously.",
                "estimated_monthly_saving": round(monthly_cost * 0.25, 2),
            }
        )

    if anomaly_count:
        recommendations.append(
            {
                "severity": "medium",
                "category": "anomaly",
                "message": f"{resource.name} has {anomaly_count} anomalous metric records. Investigate unusual workload or configuration changes.",
                "estimated_monthly_saving": 0.0,
            }
        )

    return recommendations

