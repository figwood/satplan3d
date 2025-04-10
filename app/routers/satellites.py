from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pyorbital.orbital import Orbital
from typing import List
from datetime import datetime, timedelta
import logging
from ..database import get_db
from ..schemas.base import SatelliteResponse, TLERequest
from ..dependencies import get_admin_user
from .. import models

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/satellites", response_model=List[SatelliteResponse])
def read_satellites(db: Session = Depends(get_db)):
    satellites = db.query(models.Satellite).all()
    return satellites

@router.put("/tle")
async def update_tle(
    request: TLERequest,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Validate TLE format
    lines = request.tle_data.strip().split('\n')
    if len(lines) != 3:
        raise HTTPException(status_code=400, detail="TLE must contain exactly 3 lines")

    try:
        line1 = lines[1].strip()
        line2 = lines[2].strip()
        sat_id = line1[2:7].strip()
        
        # Parse epoch from TLE line 1
        year = int(line1[18:20])
        day = float(line1[20:32])
        
        # Convert two-digit year to full year
        year = year + (2000 if year < 57 else 1900)  # Assumes years 1957-2056
        
        # Calculate timestamp from year and day
        year_start = datetime(year, 1, 1)
        tle_time = int((year_start + timedelta(days=day-1)).timestamp())
        
        orb = Orbital(sat_id, line1=line1, line2=line2)
        
        # Define time range
        start_time = tle_time
        end_time = start_time + 7 * 24 * 3600  # One week

        # Clean up old data for the same time period
        db.query(models.Track).filter(
            models.Track.noard_id == sat_id,
            models.Track.time >= start_time,
            models.Track.time <= end_time
        ).delete()
        
        # Save TLE to database
        tle = models.TLE(
            noard_id=sat_id,
            time=tle_time,
            line1=line1,
            line2=line2
        )
        db.add(tle)
        
        # Pre-calculate tracks for one week
        step = 20  # 20 seconds interval
        
        tracks = []
        for timestamp in range(start_time, end_time, step):
            try:
                dt = datetime.utcfromtimestamp(timestamp)
                # Get position and velocity
                lon, lat, alt = orb.get_lonlatalt(dt)
                # Get velocity in TEME frame (km/s)
                pos, vel = orb.get_position(dt, normalize=False)
                track = models.Track(
                    noard_id=sat_id,
                    time=timestamp,
                    lon=float(lon),
                    lat=float(lat),
                    alt=float(alt),
                    vx=float(vel[0]),
                    vy=float(vel[1]),
                    vz=float(vel[2]),
                    eci_x=float(pos[0]),
                    eci_y=float(pos[1]),
                    eci_z=float(pos[2])
                )
                tracks.append(track)
            except Exception as e:
                logger.error(f"Error calculating position at {dt}: {e}")
                continue
        
        db.bulk_save_objects(tracks)
        db.commit()
        
        return {"message": "TLE updated and tracks calculated successfully"}

    except Exception as e:
        db.rollback()  # Rollback on any error
        raise HTTPException(status_code=400, detail=str(e))