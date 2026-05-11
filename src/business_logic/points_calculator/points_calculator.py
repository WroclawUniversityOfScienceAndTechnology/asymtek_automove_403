

"""
This is demo component was created only for testing purposes
"""

import math


class Point:
    def __init__(self, label: str, x: float = 0, y: float = 0):
        self._label = label
        self._x = x
        self._y = y

    def getLabel(self) -> str:
        return self._label

    def getX(self) -> float:
        return self._x

    def getY(self) -> float:
        return self._y

    def setX(self, x: float):
        self._x = x

    def setY(self, y: float):
        self._y = y

    def __str__(self):
        return self._label + " x: " + str(self._x) + " y: " + str(self._y) + " "


class PointsDatabase:
    def __init__(self):
        self._is_connected = False
        self._points = {}

    def connect(self):
        self._is_connected = True

    def disconnect(self):
        self._is_connected = False

    def is_connected(self) -> bool:
        return self._is_connected

    def get_all(self):
        if not self.is_connected():
            raise Exception("DB not connected")

        return list(self._points.values())

    def add_point(self, point: Point):
        self._points[point.getLabel()] = point

    def clear(self):
        self._points = {}


class PointsCalc:
    def __init__(self, points_database):
        self.points_database = points_database

    @staticmethod
    def distance(p1: Point, p2: Point):
        return math.sqrt(
            ((p1.getX() - p2.getX()) ** 2) + ((p1.getY() - p2.getY()) ** 2)
        )

    @staticmethod
    def rotate(origin: Point, p: Point, angle: float):
        x = (
            math.cos(angle) * (p.getX() - origin.getX())
            - math.sin(angle) * (p.getY() - origin.getY())
            + origin.getX()
        )
        y = (
            math.sin(angle) * (p.getX() - origin.getX())
            + math.cos(angle) * (p.getY() - origin.getY())
            + origin.getY()
        )

        p.setX(x)
        p.setY(y)

    def find_closest_point(self, origin: Point) -> Point:
        points = self.points_database.get_all()
        closest = points[0]
        closest_dist = self.distance(origin, points[0])

        for p in points[1:]:
            dist = self.distance(origin, p)
            if dist < closest_dist:
                closest = p
                closest_dist = dist

        return closest

    def rotate_plane(self, origin: Point, angle: float):
        points = self.points_database.get_all()
        for point in points:
            self.rotate(origin, point, angle)
