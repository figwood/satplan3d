from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.base import OrderRequest, OrderListResponse, OrderInfoResponse
from .. import models
from datetime import datetime

router = APIRouter()

@router.get("/order/list", response_model=List[OrderListResponse])
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).all()
    return [
        OrderListResponse(
            order_name=order.order_name,
            order_id=order.id,
            hex_color=order.hex_color,
            start_time=order.start_time,
            stop_time=order.stop_time
        ) for order in orders
    ]

@router.post("/order")
async def create_order(
    request: OrderRequest,
    db: Session = Depends(get_db)
):
    # Create polygon points string from area
    area_points = [
        f"{request.area.x_min},{request.area.y_min}",  # bottom-left
        f"{request.area.x_max},{request.area.y_min}",  # bottom-right
        f"{request.area.x_max},{request.area.y_max}",  # top-right
        f"{request.area.x_min},{request.area.y_max}"   # top-left
    ]
    area_string = ";".join(area_points)

    # Create order record
    order = models.Order(
        order_time=int(datetime.now().timestamp()),
        start_time=request.start_time,
        stop_time=request.stop_time,
        area=area_string,
        sensor_ids=",".join([str(p.sensor_id) for p in request.paths]),
        order_name=request.order_name,
        hex_color=request.hex_color
    )
    db.add(order)
    db.flush()  # Get the order ID

    # Create order path records
    order_paths = []
    for path_data in request.paths:
        order_path = models.OrderPath(
            order_id=order.id,
            sensor_id=path_data.sensor_id,
            start_time=path_data.start_time,
            stop_time=path_data.stop_time,
            path=path_data.path
        )
        order_paths.append(order_path)
    
    db.bulk_save_objects(order_paths)
    db.commit()

    return {
        "message": "Order created successfully",
        "order_id": order.id
    }

@router.get("/order/{order_id}/info", response_model=OrderInfoResponse)
async def get_order_info(
    order_id: int,
    db: Session = Depends(get_db)
):
    # Get order
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get sensor IDs and query sensor details
    sensor_ids = [int(id) for id in order.sensor_ids.split(",")]
    sensors = db.query(models.Sensor).filter(models.Sensor.id.in_(sensor_ids)).all()
    
    # Get order paths
    paths = db.query(models.OrderPath).filter(
        models.OrderPath.order_id == order_id
    ).all()

    return OrderInfoResponse(
        order_id=order.id,
        order_name=order.order_name,
        order_time=order.order_time,
        start_time=order.start_time,
        stop_time=order.stop_time,
        area=order.area,
        hex_color=order.hex_color,
        sensors=[{"id": s.id, "name": s.name} for s in sensors],
        paths=[{
            "sensor_id": p.sensor_id,
            "start_time": p.start_time,
            "stop_time": p.stop_time,
            "path": p.path
        } for p in paths]
    )

@router.delete("/order/{order_id}")
async def delete_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    # Check if order exists
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        # Delete related order paths first
        db.query(models.OrderPath).filter(
            models.OrderPath.order_id == order_id
        ).delete()
        
        # Delete the order
        db.query(models.Order).filter(
            models.Order.id == order_id
        ).delete()
        
        # Commit all changes
        db.commit()
        
        return {"message": f"Order {order_id} and all related data deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/order/{order_id}")
async def update_order(
    order_id: int,
    request: OrderRequest,
    db: Session = Depends(get_db)
):
    # Check if order exists
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        # Create polygon points string from area
        area_points = [
            f"{request.area.x_min},{request.area.y_min}",  # bottom-left
            f"{request.area.x_max},{request.area.y_min}",  # bottom-right
            f"{request.area.x_max},{request.area.y_max}",  # top-right
            f"{request.area.x_min},{request.area.y_max}"   # top-left
        ]
        area_string = ";".join(area_points)

        # Update order record
        order.start_time = request.start_time
        order.stop_time = request.stop_time
        order.area = area_string
        order.sensor_ids = ",".join([str(p.sensor_id) for p in request.paths])
        order.order_name = request.order_name
        order.hex_color = request.hex_color

        # Delete existing order paths
        db.query(models.OrderPath).filter(
            models.OrderPath.order_id == order_id
        ).delete()

        # Create new order path records
        order_paths = []
        for path_data in request.paths:
            order_path = models.OrderPath(
                order_id=order_id,
                sensor_id=path_data.sensor_id,
                start_time=path_data.start_time,
                stop_time=path_data.stop_time,
                path=path_data.path
            )
            order_paths.append(order_path)
        
        db.bulk_save_objects(order_paths)
        db.commit()

        return {
            "message": "Order updated successfully",
            "order_id": order_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))