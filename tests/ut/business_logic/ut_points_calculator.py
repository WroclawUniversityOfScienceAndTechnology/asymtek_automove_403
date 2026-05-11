

"""
This file contains examples of tests using pytest
"""

import pytest
import copy

from src.business_logic.points_calculator import *
from tests.ut.business_logic.points_data import *

# Tolerance in percent (eg. 5% is 0.05)
RELATIVE_TOLERANCE = 0.001


@pytest.fixture(scope="module")
def points_database() -> PointsDatabase:
    yield PointsDatabase()


@pytest.fixture(scope="module")
def points_calc(points_database: PointsDatabase) -> PointsCalc:
    yield PointsCalc(points_database)


"""
Module scope example
- initialize db before all tests
- clear db after all tests finished
"""


@pytest.fixture(scope="module", autouse=True)
@pytest.mark.usefixtures("init_config_setup")
def init_config_setup(points_database: PointsDatabase):
    points_database.connect()
    for point in copy.deepcopy(init_points):
        points_database.add_point(point)
    yield
    points_database.clear()
    points_database.disconnect()


@pytest.mark.usefixtures("init_config_setup")
def test_database_init(points_database: PointsDatabase):
    assert points_database is not None
    assert isinstance(points_database, PointsDatabase)
    assert points_database.is_connected()
    assert len(points_database.get_all()) == len(init_points)


@pytest.mark.usefixtures("init_config_setup")
def test_calc_init(points_calc: PointsCalc):
    assert points_calc is not None
    assert isinstance(points_calc, PointsCalc)


"""
Test case parametrization example - datasets given as namedtuple
"""


@pytest.mark.usefixtures("init_config_setup")
@pytest.mark.parametrize("point_info", test_points_closest, scope="function")
def test_find_closest_point(point_info: ClosestPointInfo, points_calc: PointsCalc):
    closest = points_calc.find_closest_point(point_info.point)
    assert closest.getLabel() == point_info.closest_point


"""
Function scope example - reset db after each test
"""


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("reset_db_after_test_setup")
def reset_db_after_test_setup(points_database: PointsDatabase):
    yield
    points_database.clear()
    for point in copy.deepcopy(init_points):
        points_database.add_point(point)


"""
Floating points calculation test example
"""


@pytest.mark.usefixtures("reset_db_after_test_setup")
@pytest.mark.parametrize("rotate_point_info", test_points_rotate, scope="function")
def test_rotate(
    rotate_point_info: RotatePointInfo,
    points_calc: PointsCalc,
    points_database: PointsDatabase,
):
    def rotate(origin: Point, p: Point, angle: float) -> (float, float):
        x: float = (
            math.cos(angle) * (p.getX() - origin.getX())
            - math.sin(angle) * (p.getY() - origin.getY())
            + origin.getX()
        )
        y: float = (
            math.sin(angle) * (p.getX() - origin.getX())
            + math.cos(angle) * (p.getY() - origin.getY())
            + origin.getY()
        )
        p.setX(x)
        p.setY(y)

    db_points = points_database.get_all()
    expected_rotated_points = copy.deepcopy(db_points)
    for p in expected_rotated_points:
        rotate(rotate_point_info.rotation_origin, p, rotate_point_info.angle)

    points_calc.rotate_plane(rotate_point_info.rotation_origin, rotate_point_info.angle)

    for expected_point, actual_point in zip(expected_rotated_points, db_points):
        assert expected_point.getX() == actual_point.getX()
        assert expected_point.getY() == actual_point.getY()

    # after second rotation with angle * (-1) points should go back to init positions
    points_calc.rotate_plane(
        rotate_point_info.rotation_origin, -rotate_point_info.angle
    )

    for expected_point, actual_point in zip(init_points, db_points):
        assert expected_point.getX() == pytest.approx(
            actual_point.getX(), RELATIVE_TOLERANCE
        )
        assert expected_point.getY() == pytest.approx(
            actual_point.getY(), RELATIVE_TOLERANCE
        )


"""
Mocking example
"""


@pytest.fixture(scope="function")
def db_fake_points_mock(mocker):
    db_mock = mocker.patch(
        "src.business_logic.points_calculator.PointsDatabase.get_all"
    )
    fake_point1 = Point(label="fake_point1", x=888, y=888)
    fake_point2 = Point(label="fake_point2", x=777, y=777)
    mock_data = [fake_point1, fake_point2]
    db_mock.return_value = mock_data

    return db_mock


@pytest.mark.usefixtures("db_fake_points_mock")
def test_mocked_database(points_calc: PointsCalc, db_fake_points_mock):
    point = Point(label="p1", x=999, y=999)
    closest = points_calc.find_closest_point(point)

    db_fake_points_mock.assert_called()

    assert closest.getLabel() == "fake_point1"


@pytest.fixture(scope="function")
def disconnected_db_mock(mocker):
    db_mock = mocker.patch(
        "src.business_logic.points_calculator.PointsDatabase.is_connected"
    )
    db_mock.return_value = False

    return db_mock


"""
Exceptions example
"""


@pytest.mark.usefixtures("disconnected_db_mock")
def test_exception(points_calc: PointsCalc):
    point = Point(label="p1", x=999, y=999)
    with pytest.raises(Exception) as exception_info:
        points_calc.find_closest_point(point)

    assert "DB not connected" in str(exception_info.value)
