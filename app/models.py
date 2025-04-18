from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "sys_user"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(255))
    password = Column(String(255))
    is_admin = Column(Boolean, default=False)

class Satellite(Base):
    __tablename__ = "satellite"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    noard_id = Column(String(255), unique=True)
    name = Column(String(255))
    hex_color = Column(String(255))
    sensors = relationship("Sensor", back_populates="satellite")

class Sensor(Base):
    __tablename__ = "sensor"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sat_noard_id = Column(String(255), ForeignKey('satellite.noard_id'))
    name = Column(String(255))
    resolution = Column(Float)
    width = Column(Float)
    right_side_angle = Column(Float, default=0)
    left_side_angle = Column(Float, default=0)
    observe_angle = Column(Float)
    hex_color = Column(String(255))
    init_angle = Column(Float, default=0)
    cur_side_angle = Column(Float, default=0)
    satellite = relationship("Satellite", back_populates="sensors")

    def set_side_angle(self, angle: float):
        """设置当前侧摆角度"""
        self.cur_side_angle = angle

    @property
    def obs_angle(self) -> float:
        """For compatibility with coordinate transform code"""
        return self.observe_angle if self.observe_angle else 0

class Order(Base):
    __tablename__ = "order"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_time = Column(Integer)
    start_time = Column(Integer)
    stop_time = Column(Integer)
    area = Column(String)
    sensor_ids = Column(String)
    order_name = Column(String)
    hex_color = Column(String)

class OrderPath(Base):
    __tablename__ = "order_path"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer)
    sensor_id = Column(Integer)
    start_time = Column(Integer)
    stop_time = Column(Integer)
    path = Column(String)

class TLE(Base):
    __tablename__ = "tle"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    noard_id = Column(String(255), nullable=False, index=True)
    time = Column(Integer, nullable=False, index=True)  # timestamp
    line1 = Column(String(255), nullable=False)
    line2 = Column(String(255), nullable=False)

    def is_valid(self):
        return (
            self.line1 and 
            self.line2 and 
            isinstance(self.line1, str) and 
            isinstance(self.line2, str) and
            len(self.line1.strip()) > 0 and 
            len(self.line2.strip()) > 0
        )

class Track(Base):
    __tablename__ = "track"

    id = Column(Integer, primary_key=True)
    noard_id = Column(String(255))
    track_time = Column(Integer)
    lon = Column(Float)
    lat = Column(Float)
    alt = Column(Float)
    vx = Column(Float)
    vy = Column(Float)
    vz = Column(Float)
    eci_x = Column(Float)
    eci_y = Column(Float)
    eci_z = Column(Float)

class SensorPath(Base):
    __tablename__ = "sensor_path"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    noard_id = Column(String(255))
    sensor_id = Column(Integer)
    track_time = Column(Integer)
    lon1 = Column(Float)
    lat1 = Column(Float)
    lon2 = Column(Float)
    lat2 = Column(Float)