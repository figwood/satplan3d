from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pyorbital.orbital import Orbital
from . import models
from .database import get_db, engine
from pydantic import BaseModel
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI()

class SensorResponse(BaseModel):
    id: int
    name: str
    resolution: float | None
    width: float | None
    right_side_angle: float | None
    left_side_angle: float | None
    observe_angle: float | None
    hex_color: str | None
    init_angle: float | None

    class Config:
        from_attributes = True

class SatelliteResponse(BaseModel):
    id: int
    noard_id: str | None
    name: str | None
    hex_color: str | None
    sensors: List[SensorResponse]

    class Config:
        from_attributes = True

class TrackPoint(BaseModel):
    time: int  # timestamp
    lon: float
    lat: float
    alt: float

def get_default_time_range():
    now = int(time.time())
    return now, now + 7200  # now and now + 2 hours

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/satellites", response_model=List[SatelliteResponse])
def read_satellites(db: Session = Depends(get_db)):
    satellites = db.query(models.Satellite).all()
    return satellites

@app.get("/track-points", response_model=List[TrackPoint])
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
            # Get position
            lon, lat, alt = orb.get_lonlatalt(dt)
            track_points.append(TrackPoint(
                time=timestamp,
                lon=float(lon),
                lat=float(lat),
                alt=float(alt * 1000)  # Convert from km to meters
            ))
        except Exception as e:
            logger.error(f"Error calculating position at {dt}: {e}")
            continue

    return track_points

# Create tables
models.Base.metadata.create_all(bind=engine)