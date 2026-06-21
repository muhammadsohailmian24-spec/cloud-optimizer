from __future__ import annotations

import argparse
import socket
import time

import psutil
import requests


def collect_metrics(health_url: str = ""):
    net_before = psutil.net_io_counters()
    cpu_percent = psutil.cpu_percent(interval=1)
    net_after = psutil.net_io_counters()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    response_time_ms = 0
    if health_url:
        start = time.perf_counter()
        try:
            requests.get(health_url, timeout=10)
            response_time_ms = (time.perf_counter() - start) * 1000
        except requests.RequestException:
            response_time_ms = 10000

    return {
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory.percent, 2),
        "disk_percent": round(disk.percent, 2),
        "network_in_mb": round(max((net_after.bytes_recv - net_before.bytes_recv) / (1024 * 1024), 0), 4),
        "network_out_mb": round(max((net_after.bytes_sent - net_before.bytes_sent) / (1024 * 1024), 0), 4),
        "response_time_ms": round(response_time_ms, 2),
    }


def post_metrics(args):
    headers = {}
    if args.token:
        headers["X-Metrics-Token"] = args.token

    register_payload = {
        "name": args.name,
        "provider": args.provider,
        "resource_type": args.resource_type,
        "instance_size": socket.gethostname(),
        "region": args.region,
        "hourly_cost": args.hourly_cost,
    }
    register_response = requests.post(f"{args.optimizer_url}/api/resources/register", data=register_payload, headers=headers, timeout=20)
    register_response.raise_for_status()
    resource_id = register_response.json()["resource_id"]

    metric_payload = collect_metrics(args.health_url)
    metric_payload["resource_id"] = resource_id
    metric_response = requests.post(f"{args.optimizer_url}/api/metrics", data=metric_payload, headers=headers, timeout=20)
    metric_response.raise_for_status()
    print(f"sent {args.name}: {metric_payload}")


def main():
    parser = argparse.ArgumentParser(description="Push real server metrics to the AI Cloud Optimizer.")
    parser.add_argument("--optimizer-url", required=True, help="Example: http://18.130.208.208:8000")
    parser.add_argument("--name", required=True, help="Resource name shown on dashboard, for example app-server-13.42.48.29:4000")
    parser.add_argument("--provider", default="AWS")
    parser.add_argument("--resource-type", default="EC2 Application Server")
    parser.add_argument("--region", default="eu-west-2")
    parser.add_argument("--hourly-cost", type=float, default=0.02)
    parser.add_argument("--health-url", default="", help="Optional application URL to measure, for example http://13.42.48.29:4000")
    parser.add_argument("--token", default="")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    while True:
        post_metrics(args)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
