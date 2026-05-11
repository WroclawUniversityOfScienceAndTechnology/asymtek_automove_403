

from collections import namedtuple
from src.business_logic.points_calculator import Point
import math


init_points = [
    Point(label="p1", x=1, y=1),
    Point(label="p2", x=2.2, y=4.4),
    Point(label="p3", x=-4, y=-5),
    Point(label="p4", x=1.874, y=-10.321),
    Point(label="p5", x=-555.5, y=100.345),
]

ClosestPointInfo = namedtuple("PointInfo", "point closest_point")

test_points_closest = [
    ClosestPointInfo(point=Point(label="p", x=1, y=1), closest_point="p1"),
    ClosestPointInfo(point=Point(label="p", x=100.1, y=100.321), closest_point="p2"),
    ClosestPointInfo(point=Point(label="p", x=24.5, y=4), closest_point="p2"),
    ClosestPointInfo(point=Point(label="p", x=-89, y=-87.098), closest_point="p3"),
    ClosestPointInfo(point=Point(label="p", x=1000, y=100000), closest_point="p5"),
    ClosestPointInfo(point=Point(label="p", x=-555, y=-100), closest_point="p5"),
]

RotatePointInfo = namedtuple("PointInfo", "rotation_origin angle")

test_points_rotate = [
    RotatePointInfo(rotation_origin=Point(label="p", x=0, y=0), angle=math.pi),
    RotatePointInfo(rotation_origin=Point(label="p", x=0, y=0), angle=math.pi / 2),
    RotatePointInfo(rotation_origin=Point(label="p", x=3, y=-5), angle=0.32145),
]
