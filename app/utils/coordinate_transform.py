import numpy as np
from datetime import datetime
from typing import List, Tuple
from ..models import Sensor

class SatelliteCoordinate:
    R = 6378.15  # 地球半径（千米）

    @staticmethod
    def rotate_x(coord: np.ndarray, angle_rad: float) -> np.ndarray:
        """绕X轴旋转"""
        rot_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(angle_rad), -np.sin(angle_rad)],
            [0, np.sin(angle_rad), np.cos(angle_rad)]
        ])
        return np.dot(rot_matrix, coord)

    @staticmethod
    def rotate_z(coord: np.ndarray, angle_rad: float) -> np.ndarray:
        """绕Z轴旋转"""
        rot_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad), 0],
            [np.sin(angle_rad), np.cos(angle_rad), 0],
            [0, 0, 1]
        ])
        return np.dot(rot_matrix, coord)

    @staticmethod
    def compute_reo(r: np.ndarray, v: np.ndarray) -> np.ndarray:
        """计算从轨道坐标系到ECI坐标系的转换矩阵"""
        # 单位化
        nr = r / np.linalg.norm(r)
        nv = v / np.linalg.norm(v)
        
        # 计算H向量 (角动量方向)
        h = np.cross(nr, nv)
        
        # 计算Roe0 (速度方向)
        roe0 = np.cross(h, nr)
        
        # 构建转换矩阵
        roe = np.array([roe0, -h, -nr])
        
        # 返回矩阵的逆
        return np.linalg.inv(roe)

    def intersect_solution(self, v: np.ndarray, r: np.ndarray) -> np.ndarray:
        """计算直线与单位球面的交点"""
        # 计算二次方程系数
        A = np.dot(v, v)
        B = 2 * np.dot(v, r)
        C = np.dot(r, r) - 1

        delta = B * B - 4 * A * C
        if delta < 0:
            raise ValueError("No intersection with Earth surface")

        # 选择较近的交点
        k = (-B + np.sqrt(delta)) / (2 * A) if B > 0 else (-B - np.sqrt(delta)) / (2 * A)
        
        return r + k * v

    def get_sensor_points_eci(self, sensor: Sensor, r: np.ndarray, v: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """计算传感器观测范围在ECI坐标系中的左右边界点"""
        # 传感器本体坐标系Z轴（指向地心）
        sensor_z = np.array([0, 0, -1])  # 改为指向地心
        
        # 考虑安装角度，绕X轴旋转
        sensor_z = self.rotate_x(sensor_z, -sensor.init_angle * np.pi / 180)
        
        # 考虑侧摆角度
        side_angle = sensor.cur_side_angle * np.pi / 180
        sensor_z = self.rotate_x(sensor_z, -side_angle)
        
        # 计算观测角度
        if sensor.observe_angle and sensor.observe_angle > 0:
            obs_angle = sensor.observe_angle * np.pi / 180  # 转换为弧度
        else:
            # 根据宽度计算观测角度
            height = np.linalg.norm(r) - 1  # 相对于单位球面的高度
            if height <= 0:
                height = 0.01  # 防止高度过低
            obs_angle = np.arctan(sensor.width / (2 * height))
        
        half_angle = obs_angle / 2
        
        # 计算左右边界向量
        left_vector = self.rotate_x(sensor_z, half_angle)
        right_vector = self.rotate_x(sensor_z, -half_angle)
        
        # 计算轨道到ECI的转换矩阵
        reo = self.compute_reo(r, v)
        
        # 转换到ECI坐标系
        left_eci = np.dot(reo, left_vector)
        right_eci = np.dot(reo, right_vector)
        
        # 计算与地球表面交点
        left_point = self.intersect_solution(left_eci, r)
        right_point = self.intersect_solution(right_eci, r)
        
        return left_point, right_point

    def theta_g(self, dt: datetime) -> float:
        """计算格林尼治恒星时"""
        # 简化实现，实际应使用更精确的计算方法
        jd = self.to_julian_date(dt)
        t = (jd - 2451545.0) / 36525.0
        theta_g = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + \
                 0.000387933 * t * t - t * t * t / 38710000.0
        return np.deg2rad(theta_g % 360)

    @staticmethod
    def to_julian_date(dt: datetime) -> float:
        """将datetime转换为儒略日"""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jd = dt.day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + \
             y // 400 - 32045 + (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + \
             dt.second / 86400.0
        
        return jd

    def ecr_to_bl(self, ecr: np.ndarray) -> Tuple[float, float]:
        """将ECR坐标转换为经纬度"""
        lon = np.arctan2(ecr[1], ecr[0]) * 180 / np.pi
        lat = np.arctan2(ecr[2], np.sqrt(ecr[0]**2 + ecr[1]**2)) * 180 / np.pi
        
        # 调整经度范围到[-180, 180]
        if lon > 180:
            lon -= 360
        
        return lon, lat

    def get_sensor_points_blh(self, sensor: Sensor, dt: datetime, 
                            r: np.ndarray, v: np.ndarray) -> Tuple[float, float, float, float]:
        """计算传感器观测范围的经纬度边界"""
        # 获取ECI坐标系中的边界点
        left_eci, right_eci = self.get_sensor_points_eci(sensor, r, v)
        
        # 计算格林尼治恒星时
        theta_g = self.theta_g(dt)
        
        # 转换到ECR坐标系
        left_ecr = self.rotate_z(left_eci, -theta_g)
        right_ecr = self.rotate_z(right_eci, -theta_g)
        
        # 转换到经纬度
        left_lon, left_lat = self.ecr_to_bl(left_ecr)
        right_lon, right_lat = self.ecr_to_bl(right_ecr)
        
        return left_lon, left_lat, right_lon, right_lat