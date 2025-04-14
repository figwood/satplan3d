from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.base import ScheduleRequest
from .. import models
from datetime import datetime
from sqlalchemy import or_, and_

router = APIRouter()

@router.post("/schedule")
async def schedule_satellite(
    request: ScheduleRequest,
    db: Session = Depends(get_db)
):
    # Verify satellite and sensor exist
    satellite = db.query(models.Satellite).filter(
        models.Satellite.noard_id == request.noard_id
    ).first()
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    sensor = db.query(models.Sensor).filter(
        models.Sensor.sat_noard_id == request.noard_id,
        models.Sensor.name == request.sensor_name
    ).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # Validate time range
    if request.stop_time <= request.start_time:
        raise HTTPException(status_code=400, detail="stop_time must be after start_time")

    # Validate area boundaries
    if request.area.x_max <= request.area.x_min:
        raise HTTPException(status_code=400, detail="x_max must be greater than x_min")
    if request.area.y_max <= request.area.y_min:
        raise HTTPException(status_code=400, detail="y_max must be greater than y_min")

    # Find sensor paths that intersect with the target area during the time window
    paths = db.query(models.SensorPath).filter(
        models.SensorPath.track_time >= request.start_time,
        models.SensorPath.track_time <= request.stop_time,
        models.SensorPath.sensor_id == sensor.id,
        or_(
            # First point inside the area
            and_(
                models.SensorPath.lon1 > request.area.x_min,
                models.SensorPath.lon1 < request.area.x_max,
                models.SensorPath.lat1 > request.area.y_min,
                models.SensorPath.lat1 < request.area.y_max
            ),
            # Or second point inside the area
            and_(
                models.SensorPath.lon2 > request.area.x_min,
                models.SensorPath.lon2 < request.area.x_max,
                models.SensorPath.lat2 > request.area.y_min,
                models.SensorPath.lat2 < request.area.y_max
            )
        )
    ).order_by(models.SensorPath.track_time).all()

    if not paths:
        return {
            "message": "No available observation opportunities found",
            "satellite": request.noard_id,
            "sensor": request.sensor_name
        }

    # Group paths into observation opportunities
    # An opportunity is a continuous sequence of paths that cover the area
    opportunities = []
    current_opportunity = []
    last_time = None
    
    for path in paths:
        if last_time is None or path.track_time - last_time <= 20:  # 20 seconds is our sampling interval
            current_opportunity.append(path)
        else:
            if current_opportunity:
                opportunities.append(current_opportunity)
            current_opportunity = [path]
        last_time = path.track_time

    if current_opportunity:
        opportunities.append(current_opportunity)

    # Format response with observation opportunities
    schedule_response = []
    for opportunity in opportunities:
        # 收集所有点并按逆时针顺序排列
        polygon_points = []
        # 首先添加所有右侧点（从前到后）
        for path in opportunity:
            polygon_points.append({"lon": path.lon2, "lat": path.lat2})
        # 然后添加所有左侧点（从后到前）
        for path in reversed(opportunity):
            polygon_points.append({"lon": path.lon1, "lat": path.lat1})
            
        schedule_response.append({
            "start_time": opportunity[0].track_time,
            "end_time": opportunity[-1].track_time,
            "polygon": polygon_points
        })

    return {
        "message": f"Found {len(opportunities)} observation opportunities",
        "satellite": request.noard_id,
        "sensor": request.sensor_name,
        "opportunities": schedule_response
    }