from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pyorbital.orbital import Orbital
from . import models
from .database import get_db, engine
from .security import verify_password, create_access_token, get_password_hash, SECRET_KEY, ALGORITHM
from pydantic import BaseModel
from datetime import datetime, timedelta
import time
import logging
from jose import jwt, JWTError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
    vx: float
    vy: float
    vz: float

class TLERequest(BaseModel):
    tle_data: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

def get_default_time_range():
    now = int(time.time())
    return now, now + 7200  # now and now + 2 hours

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.user_name == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission required"
        )
    return current_user

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/satellites", response_model=List[SatelliteResponse])
def read_satellites(db: Session = Depends(get_db)):
    satellites = db.query(models.Satellite).all()
    return satellites

@app.put("/tle")
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
                # Get velocity in TEME frame (m/s)
                pos, vel = orb.get_position(dt, normalize=False)
                track = models.Track(
                    noard_id=sat_id,
                    time=timestamp,
                    lon=float(lon),
                    lat=float(lat),
                    alt=float(alt * 1000),  # Convert from km to meters
                    vx=float(vel[0] * 1000),  # Convert from km/s to m/s
                    vy=float(vel[1] * 1000),
                    vz=float(vel[2] * 1000)
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

    # First try to get tracks from database
    tracks = db.query(models.Track).filter(
        models.Track.noard_id == noard_id,
        models.Track.time >= start_time,
        models.Track.time <= stop_time
    ).order_by(models.Track.time).all()

    if tracks:
        return [TrackPoint(
            time=track.time,
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

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.debug(f"Login attempt for username: {form_data.username}")
    
    user = db.query(models.User).filter(models.User.user_name == form_data.username).first()
    if not user:
        logger.debug(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Found user: {user.user_name}")
    logger.debug(f"Stored hashed password: {user.password}")
    logger.debug(f"Attempting to verify password...")
    
    if not verify_password(form_data.password, user.password):
        logger.debug("Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug("Password verified successfully")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.user_name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    current_user.password = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

# Create tables
models.Base.metadata.create_all(bind=engine)