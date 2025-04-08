from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from . import models
from .database import get_db, engine
from pydantic import BaseModel

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
        orm_mode = True

class SatelliteResponse(BaseModel):
    id: int
    noard_id: str | None
    name: str | None
    hex_color: str | None
    sensors: List[SensorResponse]

    class Config:
        orm_mode = True

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/satellites", response_model=List[SatelliteResponse])
def read_satellites(db: Session = Depends(get_db)):
    satellites = db.query(models.Satellite).all()
    return satellites

# Create tables
models.Base.metadata.create_all(bind=engine)