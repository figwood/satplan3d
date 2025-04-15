from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pyorbital.orbital import Orbital
from typing import List
from datetime import datetime, timedelta
import logging, numpy as np
from ..database import get_db
from ..schemas.base import SatelliteResponse, TLERequest, SatelliteCreate, SatelliteUpdate, SensorCreate, SensorUpdate, SensorResponse
from ..dependencies import get_admin_user
from .. import models
from ..utils.coordinate_transform import SatelliteCoordinate

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/satellite/list", response_model=List[SatelliteResponse])
def read_satellites(db: Session = Depends(get_db)):
    satellites = db.query(models.Satellite).all()
    return satellites

@router.post("/satellite", response_model=SatelliteResponse)
async def create_satellite(
    request: SatelliteCreate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Validate TLE format
    lines = request.tle.strip().split('\n')
    if len(lines) != 3:
        raise HTTPException(status_code=400, detail="TLE must contain exactly 3 lines")

    try:
        line1 = lines[1].strip()
        line2 = lines[2].strip()
        sat_id = line1[2:7].strip()

        # Check if satellite already exists
        existing_satellite = db.query(models.Satellite).filter(
            models.Satellite.noard_id == sat_id
        ).first()
        if existing_satellite:
            raise HTTPException(
                status_code=400,
                detail=f"Satellite with NORAD ID {sat_id} already exists"
            )

        # Create new satellite
        satellite = models.Satellite(
            noard_id=sat_id,
            name=request.sat_name,
            hex_color=request.hex_color
        )
        db.add(satellite)

        # Parse epoch from TLE line 1
        year = int(line1[18:20])
        day = float(line1[20:32])
        
        # Convert two-digit year to full year
        year = year + (2000 if year < 57 else 1900)  # Assumes years 1957-2056
        
        # Calculate timestamp from year and day
        year_start = datetime(year, 1, 1)
        tle_time = int((year_start + timedelta(days=day-1)).timestamp())

        # Save TLE to database
        tle = models.TLE(
            noard_id=sat_id,
            time=tle_time,
            line1=line1,
            line2=line2
        )
        db.add(tle)
        
        # Commit to get the satellite ID
        db.commit()
        db.refresh(satellite)

        # Calculate initial tracks using the update_tle logic
        tle_request = TLERequest(tle_data=request.tle)
        await update_tle(tle_request, admin_user, db)
        
        return satellite

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/satellite/{noard_id}", response_model=SatelliteResponse)
async def update_satellite(
    noard_id: str,
    request: SatelliteUpdate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if satellite exists
        satellite = db.query(models.Satellite).filter(
            models.Satellite.noard_id == noard_id
        ).first()
        
        if not satellite:
            raise HTTPException(
                status_code=404,
                detail=f"Satellite with NORAD ID {noard_id} not found"
            )

        # Update satellite information
        satellite.name = request.sat_name
        satellite.hex_color = request.hex_color
        
        # Commit changes
        db.commit()
        db.refresh(satellite)
        
        return satellite

    except Exception as e:
        db.rollback()  # Rollback on any error
        raise HTTPException(status_code=400, detail=str(e))

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

        # Clean up old data
        db.query(models.Track).filter(
            models.Track.noard_id == sat_id,
            models.Track.track_time >= start_time,
            models.Track.track_time <= end_time
        ).delete()

        db.query(models.SensorPath).filter(
            models.SensorPath.noard_id == sat_id,
            models.SensorPath.track_time >= start_time,
            models.SensorPath.track_time <= end_time
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
        coord_calculator = SatelliteCoordinate()
        
        tracks = []
        sensor_paths = []

        # Get all sensors for this satellite
        sensors = db.query(models.Sensor).filter(
            models.Sensor.sat_noard_id == sat_id
        ).all()
        
        for timestamp in range(start_time, end_time, step):
            try:
                dt = datetime.utcfromtimestamp(timestamp)
                # Get position and velocity
                lon, lat, alt = orb.get_lonlatalt(dt)
                # Get velocity in TEME frame (km/s)
                pos, vel = orb.get_position(dt, normalize=False)
                
                # Create track point
                track = models.Track(
                    noard_id=sat_id,
                    track_time=timestamp,
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

                # Calculate sensor paths
                r = np.array([pos[0], pos[1], pos[2]]) / coord_calculator.R
                v = np.array([vel[0], vel[1], vel[2]]) / coord_calculator.R

                for sensor in sensors:
                    try:
                        left_lon, left_lat, right_lon, right_lat = coord_calculator.get_sensor_points_blh(
                            sensor, dt, r, v
                        )
                        
                        # Store both points in one record
                        sensor_paths.append(models.SensorPath(
                            noard_id=sat_id,
                            sensor_id=sensor.id,
                            track_time=timestamp,
                            lon1=left_lon,
                            lat1=left_lat,
                            lon2=right_lon,
                            lat2=right_lat
                        ))
                    except Exception as e:
                        logger.error(f"Error calculating sensor path for sensor {sensor.id} at {dt}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error calculating position at {dt}: {e}")
                continue
        
        # Save all data
        db.bulk_save_objects(tracks)
        db.bulk_save_objects(sensor_paths)
        db.commit()
        
        return {"message": "TLE updated, tracks and sensor paths calculated successfully"}

    except Exception as e:
        db.rollback()  # Rollback on any error
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/satellite/{noard_id}")
async def delete_satellite(
    noard_id: str,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if satellite exists
        satellite = db.query(models.Satellite).filter(
            models.Satellite.noard_id == noard_id
        ).first()
        
        if not satellite:
            raise HTTPException(
                status_code=404,
                detail=f"Satellite with NORAD ID {noard_id} not found"
            )

        # Delete all related records
        # Delete sensor paths
        db.query(models.SensorPath).filter(
            models.SensorPath.noard_id == noard_id
        ).delete()
        
        # Delete tracks
        db.query(models.Track).filter(
            models.Track.noard_id == noard_id
        ).delete()
        
        # Delete TLEs
        db.query(models.TLE).filter(
            models.TLE.noard_id == noard_id
        ).delete()
        
        # Delete sensors
        db.query(models.Sensor).filter(
            models.Sensor.sat_noard_id == noard_id
        ).delete()
        
        # Delete the satellite itself
        db.query(models.Satellite).filter(
            models.Satellite.noard_id == noard_id
        ).delete()

        # Commit all changes
        db.commit()
        
        return {"message": f"Satellite {noard_id} and all related data deleted successfully"}

    except Exception as e:
        db.rollback()  # Rollback on any error
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sensor", response_model=SensorResponse)
async def create_sensor(
    request: SensorCreate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if satellite exists
        satellite = db.query(models.Satellite).filter(
            models.Satellite.noard_id == request.noard_id
        ).first()
        
        if not satellite:
            raise HTTPException(
                status_code=404,
                detail=f"Satellite with NORAD ID {request.noard_id} not found"
            )

        # Check if sensor name already exists for this satellite
        existing_sensor = db.query(models.Sensor).filter(
            models.Sensor.sat_noard_id == request.noard_id,
            models.Sensor.name == request.sensor_name
        ).first()
        
        if existing_sensor:
            raise HTTPException(
                status_code=400,
                detail=f"Sensor with name {request.sensor_name} already exists for this satellite"
            )

        # Create new sensor
        sensor = models.Sensor(
            sat_noard_id=request.noard_id,
            name=request.sensor_name,
            resolution=request.resolution,
            right_side_angle=request.right_side_angle,
            left_side_angle=request.left_side_angle,
            init_angle=request.init_angle,
            observe_angle=request.observe_angle,
            hex_color=request.hex_color
        )
        
        db.add(sensor)
        db.commit()
        db.refresh(sensor)
        
        return sensor

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/sensor/{sensor_id}", response_model=SensorResponse)
async def update_sensor(
    sensor_id: int,
    request: SensorUpdate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        # Find the sensor by ID
        sensor = db.query(models.Sensor).filter(
            models.Sensor.id == sensor_id
        ).first()
        
        if not sensor:
            raise HTTPException(
                status_code=404,
                detail=f"Sensor with ID {sensor_id} not found"
            )

        # If sensor name is being changed, check for conflicts
        if request.sensor_name != sensor.name:
            existing_sensor = db.query(models.Sensor).filter(
                models.Sensor.sat_noard_id == sensor.sat_noard_id,
                models.Sensor.name == request.sensor_name
            ).first()
            
            if existing_sensor:
                raise HTTPException(
                    status_code=400,
                    detail=f"Sensor with name {request.sensor_name} already exists for this satellite"
                )

        # Update sensor information
        sensor.name = request.sensor_name
        sensor.resolution = request.resolution
        sensor.right_side_angle = request.right_side_angle
        sensor.left_side_angle = request.left_side_angle
        sensor.init_angle = request.init_angle
        sensor.observe_angle = request.observe_angle
        sensor.hex_color = request.hex_color
        
        db.commit()
        db.refresh(sensor)
        
        return sensor

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sensor/{sensor_id}")
async def delete_sensor(
    sensor_id: int,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        # Find the sensor by ID
        sensor = db.query(models.Sensor).filter(
            models.Sensor.id == sensor_id
        ).first()
        
        if not sensor:
            raise HTTPException(
                status_code=404,
                detail=f"Sensor with ID {sensor_id} not found"
            )

        # Delete all related sensor paths
        db.query(models.SensorPath).filter(
            models.SensorPath.sensor_id == sensor_id
        ).delete()
        
        # Delete the sensor
        db.query(models.Sensor).filter(
            models.Sensor.id == sensor_id
        ).delete()
        
        # Commit all changes
        db.commit()
        
        return {"message": f"Sensor with ID {sensor_id} and all related data deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))