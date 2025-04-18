from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class TLERequest(BaseModel):
    tle_data: str

class TLEUpdateResponse(BaseModel):
    message: str

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

class SensorCreate(BaseModel):
    noard_id: str
    sensor_name: str
    resolution: float
    right_side_angle: float
    left_side_angle: float
    init_angle: float
    observe_angle: float
    hex_color: str

    class Config:
        from_attributes = True

class SensorUpdate(BaseModel):
    sensor_name: str
    resolution: float
    right_side_angle: float
    left_side_angle: float
    init_angle: float
    observe_angle: float
    hex_color: str

    class Config:
        from_attributes = True

class SatelliteResponse(BaseModel):
    id: int
    noard_id: str | None
    name: str | None
    hex_color: str | None
    latest_tle_time: int | None
    sensors: List[SensorResponse]

    class Config:
        from_attributes = True

class SatelliteCreate(BaseModel):
    sat_name: str
    hex_color: str
    tle: str

class SatelliteUpdate(BaseModel):
    sat_name: str
    hex_color: str

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

class CoveragePoint(BaseModel):
    time: int
    lon: float
    lat: float

class PathPoint(BaseModel):
    time: int
    lon1: float
    lat1: float
    lon2: float
    lat2: float

class SensorBrief(BaseModel):
    id: int
    name: str

class OrderListResponse(BaseModel):
    order_name: str
    order_id: int
    hex_color: str

    class Config:
        from_attributes = True

class OrderPathResponse(BaseModel):
    sensor_id: int
    start_time: int
    stop_time: int
    path: str

class OrderInfoResponse(BaseModel):
    order_id: int
    order_name: str
    order_time: int
    start_time: int
    stop_time: int
    area: str
    hex_color: str
    sensors: List[SensorBrief]
    paths: List[OrderPathResponse]

    class Config:
        from_attributes = True

class Area(BaseModel):
    x_min: float
    x_max: float
    y_min: float
    y_max: float

class OrderPath(BaseModel):
    sensor_id: int
    start_time: int
    stop_time: int
    path: str

class OrderRequest(BaseModel):
    order_name: str
    start_time: int
    stop_time: int
    area: Area
    paths: List[OrderPath]
    hex_color: str

class ScheduleRequest(BaseModel):
    noard_id: str
    sensor_name: str
    start_time: int
    stop_time: int
    area: Area
