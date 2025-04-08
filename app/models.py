from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "sys_user"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(255))
    password = Column(String(255))

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
    sat_name = Column(String(255))
    name = Column(String(255))
    resolution = Column(Float)
    width = Column(Float)
    right_side_angle = Column(Float)
    left_side_angle = Column(Float)
    observe_angle = Column(Float)
    hex_color = Column(String(255))
    init_angle = Column(Float)
    satellite = relationship("Satellite", back_populates="sensors")

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
    time = Column(Integer)
    lon = Column(Float)
    lat = Column(Float)
    alt = Column(Float)