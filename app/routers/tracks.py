from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..schemas.base import TrackPoint, PathPoint
from typing import List, Optional
from pyorbital.orbital import Orbital
from .. import models
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/track-points", response_model=List[TrackPoint])
async def get_track_points(
    noard_id: str,
    start_time: Optional[int] = Query(None, description="Start timestamp in UTC"),
    stop_time: Optional[int] = Query(None, description="Stop timestamp in UTC"),
    db: Session = Depends(get_db)
):
    # Handle default times (in UTC)
    if start_time is None:
        start_time = int(datetime.utcnow().timestamp())
        stop_time = stop_time or (start_time + 7200)  # 2 hours from start
    elif stop_time is None:
        stop_time = start_time + 7200  # 2 hours from start

    # Validate times
    if stop_time <= start_time:
        raise HTTPException(status_code=400, detail="stop_time must be after start_time")

    # First try to get tracks from database
    tracks = db.query(models.Track).filter(
        models.Track.noard_id == noard_id,
        models.Track.track_time >= start_time,
        models.Track.track_time <= stop_time
    ).order_by(models.Track.track_time).all()

    if tracks:
        return [TrackPoint(
            time=track.track_time,
            lon=track.lon,
            lat=track.lat,
            alt=track.alt,
            vx=track.vx,
            vy=track.vy,
            vz=track.vz
        ) for track in tracks]

    # If no tracks found, fall back to real-time calculation
    # Get the closest TLE data by absolute time difference
    tle_data = db.query(models.TLE).filter(
        models.TLE.noard_id == noard_id
    ).order_by(
        func.abs(models.TLE.time - start_time)
    ).first()

    if not tle_data or not tle_data.is_valid():
        raise HTTPException(status_code=404, detail="No valid TLE data found for this satellite")

    # Initialize orbital computations
    try:
        # Ensure TLE lines are properly formatted strings
        line1 = tle_data.line1.strip()
        line2 = tle_data.line2.strip()
        # Extract satellite name from TLE line 1 (columns 3-7 contain the satellite ID)
        sat_id = line1[2:7].strip()
        orb = Orbital(sat_id, line1=line1, line2=line2)
    except Exception as e:
        logger.error(f"Invalid TLE data for satellite {noard_id}: {str(e)}\nline1: {line1}\nline2: {line2}")
        raise HTTPException(status_code=400, detail=f"Invalid TLE data format: {str(e)}")

    # Calculate positions every 20 seconds
    track_points = []
    step = 20  # 20 seconds interval
    
    for timestamp in range(start_time, stop_time, step):
        try:
            # Convert UTC timestamp to datetime
            dt = datetime.utcfromtimestamp(timestamp)
            # Get position and velocity
            lon, lat, alt = orb.get_lonlatalt(dt)
            pos, vel = orb.get_position(dt, normalize=False)
            track_points.append(TrackPoint(
                time=timestamp,
                lon=float(lon),
                lat=float(lat),
                alt=float(alt * 1000),  # Convert from km to meters
                vx=float(vel[0] * 1000),  # Convert from km/s to m/s
                vy=float(vel[1] * 1000),
                vz=float(vel[2] * 1000)
            ))
        except Exception as e:
            logger.error(f"Error calculating position at {dt}: {e}")
            continue

    return track_points

@router.get("/path-points", response_model=List[PathPoint])
async def get_path_points(
    noard_id: str,
    sensor_name: str,
    start_time: Optional[int] = Query(None, description="Start timestamp in UTC"),
    stop_time: Optional[int] = Query(None, description="Stop timestamp in UTC"),
    db: Session = Depends(get_db)
):
    # Handle default times (in UTC)
    if start_time is None:
        start_time = int(datetime.utcnow().timestamp())
        stop_time = stop_time or (start_time + 7200)  # 2 hours from start
    elif stop_time is None:
        stop_time = start_time + 7200  # 2 hours from start

    # Validate times
    if stop_time <= start_time:
        raise HTTPException(status_code=400, detail="stop_time must be after start_time")

    # Get sensor id
    sensor = db.query(models.Sensor).filter(
        models.Sensor.sat_noard_id == noard_id,
        models.Sensor.name == sensor_name
    ).first()
    
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # Get path points from database
    paths = db.query(models.SensorPath).filter(
        models.SensorPath.noard_id == noard_id,
        models.SensorPath.sensor_id == sensor.id,
        models.SensorPath.track_time >= start_time,
        models.SensorPath.track_time <= stop_time
    ).order_by(models.SensorPath.track_time).all()

    if not paths:
        raise HTTPException(status_code=404, detail="No path data found for this time period")

    return [PathPoint(
        time=path.track_time,
        lon1=path.lon1,
        lat1=path.lat1,
        lon2=path.lon2,
        lat2=path.lat2
    ) for path in paths]