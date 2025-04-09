from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.base import CoveragePoint
from typing import List, Optional
from .. import models

router = APIRouter()

@router.get("/coverage", response_model=List[CoveragePoint])
async def get_coverage(
    noard_id: str,
    sensor_name: str,
    side_angle: float = Query(0.0, description="Side angle for coverage calculation"),
    start_time: Optional[int] = Query(None, description="Start timestamp in UTC"),
    stop_time: Optional[int] = Query(None, description="Stop timestamp in UTC"),
    db: Session = Depends(get_db)
):
    # Handle default times (in UTC)
    if start_time is None:
        start_time = int(datetime.utcnow().timestamp())
        stop_time = stop_time or (start_time + 7200)  # 2 hours from start
    elif stop_time is None:
        stop_time = start_time + 7200  # 2 hours from specified start

    # Validate times
    if stop_time <= start_time:
        raise HTTPException(status_code=400, detail="stop_time must be after start_time")

    # Verify satellite and sensor exist
    satellite = db.query(models.Satellite).filter(models.Satellite.noard_id == noard_id).first()
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    sensor = db.query(models.Sensor).filter(
        models.Sensor.satellite_id == satellite.id,
        models.Sensor.name == sensor_name
    ).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # TODO: Implement coverage calculation
    # This is a placeholder that will return empty list until implementation is provided
    coverage_points = []
    
    return coverage_points