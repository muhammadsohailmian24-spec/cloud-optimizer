from __future__ import annotations

from app.models import CloudResource


def upsert_resource(
    db,
    name: str,
    provider: str = "Remote",
    resource_type: str = "Application Server",
    instance_size: str = "unknown",
    region: str = "unknown",
    hourly_cost: float = 0.02,
) -> CloudResource:
    resource = db.query(CloudResource).filter(CloudResource.name == name).first()
    if resource:
        resource.provider = provider
        resource.resource_type = resource_type
        resource.instance_size = instance_size
        resource.region = region
        resource.hourly_cost = hourly_cost
    else:
        resource = CloudResource(
            name=name,
            provider=provider,
            resource_type=resource_type,
            instance_size=instance_size,
            region=region,
            hourly_cost=hourly_cost,
        )
        db.add(resource)

    db.commit()
    db.refresh(resource)
    return resource

