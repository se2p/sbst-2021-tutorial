from shapely.geometry import Point


class TargetAreaOracle():

    def __init__(self, target_position, radius, state_sensor):
        self.targer_position = Point(target_position)
        self.radius = radius
        self.state_sensor = state_sensor

    def check(self):
        distance_to_goal = self.targer_position.distance(Point(self.state_sensor.data['pos']))
        # print("Distance to target", distance_to_goal)
        return distance_to_goal < self.radius


class DamagedOracle():
    def __init__(self, damage_sensor):
        self.damage_sensor = damage_sensor

    def check(self):
        return len(self.damage_sensor.data['part_damage']) > 0

class OBEOracle():
    # TODO
    def __init__(self, road_geometry, state_sensor):
        self.state_sensor = state_sensor
        self.road_geometry = road_geometry

    def check(self):
        # get car position, check if inside the right lane poligon
        return False
