from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100), index=True)

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