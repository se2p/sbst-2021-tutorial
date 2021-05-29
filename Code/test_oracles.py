from shapely.geometry import Point, Polygon, LineString
import numpy as np


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



class RoadPolygon:
    """A class that represents the road as a geometrical object
    (a polygon or a sequence of polygons)."""

    @classmethod
    def from_nodes(cls, nodes):
        return RoadPolygon(RoadPoints.from_nodes(nodes))

    def __init__(self, road_points):
        assert len(road_points.left) == len(road_points.right) == len(road_points.middle)
        assert len(road_points.left) >= 2
        assert all(len(x) == 4 for x in road_points.middle)
        assert all(len(x) == 2 for x in road_points.left)
        assert all(len(x) == 2 for x in road_points.right)
        assert all(x[3] == road_points.middle[0][3] for x in
                   road_points.middle), "The width of the road should be equal everywhere."
        self.road_points = road_points
        self.road_width = road_points.middle[0][3]
        self.polygons = self._compute_polygons()
        self.polygon = self._compute_polygon()
        self.right_polygon = self._compute_right_polygon()
        self.left_polygon = self._compute_left_polygon()
        self.polyline = self._compute_polyline()
        self.right_polyline = self._compute_right_polyline()
        self.left_polyline = self._compute_left_polyline()
        self.num_polygons = len(self.polygons)

    def _compute_polygons(self):
        """Creates and returns a list of Polygon objects that represent the road.
        Each polygon represents a segment of the road. Two objects adjacent in
        the returned list represent adjacent segments of the road."""
        polygons = []
        for left, right, left1, right1, in zip(self.road_points.left,
                                               self.road_points.right,
                                               self.road_points.left[1:],
                                               self.road_points.right[1:]):
            assert len(left) >= 2 and len(right) >= 2 and len(left1) >= 2 and len(right1) >= 2
            # Ignore the z coordinate.
            polygons.append(Polygon([left[:2], left1[:2], right1[:2], right[:2]]))
        return polygons

    def _compute_polygon(self):
        """Returns a single polygon that represents the whole road."""
        road_poly = self.road_points.left.copy()
        road_poly.extend(self.road_points.right[::-1])
        return Polygon(road_poly)

    def _compute_right_polygon(self):
        """Returns a single polygon that represents the right lane of the road."""
        road_poly = [(p[0], p[1]) for p in self.road_points.middle]
        road_poly.extend(self.road_points.right[::-1])
        return Polygon(road_poly)

    def _compute_left_polygon(self):
        """Returns a single polygon that represents the left lane of the road."""
        road_poly = self.road_points.left.copy()
        road_poly.extend([(p[0], p[1]) for p in self.road_points.middle][::-1])
        return Polygon(road_poly)

    def _compute_polyline(self):
        """Computes and returns a LineString representing the polyline
        of the spin (or middle) of the road."""
        return LineString([(n[0], n[1]) for n in self.road_points.middle])

    def _compute_right_polyline(self):
        """Computes and returns a LineString representing the polyline
        of the spin (or middle) of the right lane of the road."""
        return LineString([((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2) for p1, p2 in
                           zip(self.road_points.middle, self.road_points.right)])

    def _compute_left_polyline(self):
        """Computes and returns a LineString representing the polyline
        of the spin (or middle) of the left lane of the road."""
        return LineString([((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2) for p1, p2 in
                           zip(self.road_points.left, self.road_points.middle)])

    def _get_neighbouring_polygons(self, i: int):
        """Returns the indices of the neighbouring polygons of the polygon
        with index i."""
        if self.num_polygons == 1:
            assert i == 0
            return None
        assert 0 <= i < self.num_polygons
        if i == 0:
            return [i + 1]
        elif i == self.num_polygons - 1:
            return [i - 1]
        else:
            assert self.num_polygons >= 3
            return [i - 1, i + 1]

    def _are_neighbouring_polygons(self, i: int, j: int):
        """Returns true if the polygons represented by the indices i and j are adjacent."""
        return j in self._get_neighbouring_polygons(i)

    def is_valid(self):
        """Returns true if the current RoadPolygon representation of the road is valid,
        that is, if there are no intersections between non-adjacent polygons and if
        the adjacent polygons have as intersection a LineString (a line or segment)."""
        if self.num_polygons == 0:
            print("No polygon constructed.")
            return False

        for i, polygon in enumerate(self.polygons):
            if not polygon.is_valid:
                # logging.debug("Polygon %s is invalid." % polygon)
                print("Polygon is invalid")
                return False

        for i, polygon in enumerate(self.polygons):
            for j, other in enumerate(self.polygons):
                # Ignore the case when other is equal to the polygon.
                if other == polygon:
                    assert i == j
                    continue
                if polygon.contains(other) or other.contains(polygon):
                    # logging.debug("No polygon should contain any other polygon.")
                    print("The road is apparently valid.")
                    return False
                if not self._are_neighbouring_polygons(i, j) and other.intersects(polygon):
                    # logging.debug("The non-neighbouring polygons %s and %s intersect." % (polygon, other))
                    print("The road is apparently valid.")
                    return False
                if self._are_neighbouring_polygons(i, j) and not isinstance(other.intersection(polygon), LineString):
                    # logging.debug("The neighbouring polygons %s and %s have an intersection of type %s." % (
                    #     polygon, other, type(other.intersection(polygon))))
                    print("The road is apparently valid.")
                    return False
        print("The road is apparently valid.")
        return True


class RoadPoints:

    @classmethod
    def from_nodes(cls, middle_nodes):
        res = RoadPoints()
        res.add_middle_nodes(middle_nodes)
        return res

    def __init__(self):
        self.middle = []
        self.right = []
        self.left = []
        self.n = 0

    def add_middle_nodes(self, middle_nodes):
        n = len(self.middle) + len(middle_nodes)

        assert n >= 2, f'At least, two nodes are needed'

        assert all(len(point) >= 4 for point in middle_nodes), \
            f'A node is a tuple of 4 elements (x,y,z,road_width)'

        self.n = n
        self.middle += list(middle_nodes)
        self.left += [None] * len(middle_nodes)
        self.right += [None] * len(middle_nodes)
        self._recalculate_nodes()
        return self

    def _recalculate_nodes(self):
        for i in range(self.n - 1):
            l, r = self.calc_point_edges(self.middle[i], self.middle[i + 1])
            self.left[i] = l
            self.right[i] = r

        # the last middle point
        self.right[-1], self.left[-1] = self.calc_point_edges(self.middle[-1], self.middle[-2])

    @classmethod
    def calc_point_edges(cls, p1, p2):
        origin = np.array(p1[0:2])

        a = np.subtract(p2[0:2], origin)

        #TODO: changed from 2 to 4
        # calculate the vector which length is half the road width
        v = (a / np.linalg.norm(a)) * p1[3] / 2
        # add normal vectors
        l = origin + np.array([-v[1], v[0]])
        r = origin + np.array([v[1], -v[0]])
        return tuple(l), tuple(r)

class SimpleOBEOracle():
    """
        Returns true if the car is out of the right lane out-of-bound (OOB).
        It assumes a road formed with two lanes
    """

    def __init__(self, road_nodes, state_sensor):
        self.state_sensor = state_sensor
        # Extract Polygon of the right lane
        self.road_polygon = RoadPolygon.from_nodes(road_nodes)

    def check(self):
        car_position = Point(self.state_sensor.data['pos'])
        return not self.road_polygon.right_polygon.contains(car_position)
