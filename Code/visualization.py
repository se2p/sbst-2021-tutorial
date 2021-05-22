# This code comes from the SBST Tool competition
from matplotlib import pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import LineString, Polygon
from shapely.affinity import translate, rotate
from descartes import PolygonPatch
from math import atan2, pi, degrees
from scipy.interpolate import splev, splprep
from numpy.ma import arange
from beamngpy import Road

from scipy.spatial.transform import Rotation as R
from numpy import linspace, array, cross, dot
from shapely.geometry import LineString, Point
from shapely.affinity import translate, rotate, scale
from scipy.spatial import geometric_slerp
from math import sin, cos, radians, degrees, atan2, copysign
import common
from notescratch import generate_road_nodes

# Constants
rounding_precision = 3
interpolation_distance = 1
smoothness = 0
min_num_nodes = 20

# Trajectory generation
def _interpolate(nodes):
    """
        Interpolate the road points using cubic splines and ensure we handle 4F tuples for compatibility
    """
    old_x_vals = [t[0] for t in nodes]
    old_y_vals = [t[1] for t in nodes]

    # This is an approximation based on whatever input is given
    test_road_lenght = LineString([(t[0], t[1]) for t in nodes]).length
    num_nodes = int(test_road_lenght / interpolation_distance)
    if num_nodes < min_num_nodes:
        num_nodes = min_num_nodes

    assert len(old_x_vals) >= 2, "You need at leas two road points to define a road"
    assert len(old_y_vals) >= 2, "You need at leas two road points to define a road"

    if len(old_x_vals) == 2:
        # With two points the only option is a straight segment
        k = 1
    elif len(old_x_vals) == 3:
        # With three points we use an arc, using linear interpolation will result in invalid road tests
        k = 2
    else:
        # Otheriwse, use cubic splines
        k = 3

    pos_tck, pos_u = splprep([old_x_vals, old_y_vals], s= smoothness, k=k)

    step_size = 1 / num_nodes
    unew = arange(0, 1 + step_size, step_size)

    new_x_vals, new_y_vals = splev(unew, pos_tck)

    # Return the 4-tuple with default z and defatul road width
    return list(zip([round(v, rounding_precision) for v in new_x_vals],
                    [round(v, rounding_precision) for v in new_y_vals]))

# https://stackoverflow.com/questions/1560492/how-to-tell-whether-a-point-is-to-the-right-or-left-side-of-a-line
# Where a = line point 1; b = line point 2; c = point to check against.
def isLeft(a, b, c):
    return ((b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x)) > 0;

# https://stackoverflow.com/questions/34764535/why-cant-matplotlib-plot-in-a-different-thread
class RoadVisualizer:
    """
        Visualize and Plot RoadTests
    """

    little_triangle = Polygon([(10, 0), (0, -5), (0, 5), (10, 0)])
    square = Polygon([(5, 5), (5, -5), (-5, -5), (-5, 5), (5, 5)])

    # def __init__(self):
        # Make sure there's a windows and does not block anything when calling show
        # plt.ion()
        # plt.show()
        # pass

    def visualize_road(self, road):

        # Adapt the size of the map to the road
        min_x = min([node[0] for node in road.nodes])
        max_x = max([node[0] for node in road.nodes])
        min_y = min([node[1] for node in road.nodes])
        max_y = max([node[1] for node in road.nodes])

        map_size = max((max_x - min_x), (max_y - min_y))

        plt.gca().set_aspect('equal', 'box')
        plt.gca().set(xlim=(-50 + min_x, max_x + 50), ylim=(-50 + min_y, max_y + 50))

        # Plot the map. Trying to re-use an artist in more than one Axes which is supported
        # map_patch = patches.Rectangle((0, 0), map_size, map_size,
        #                               linewidth=1, edgecolor='black',
        #                               facecolor='none')
        # plt.gca().add_patch(map_patch)

        # Road Geometry.
        interpolated_points = _interpolate(road.nodes)
        road_spine = LineString([(t[0], t[1]) for t in interpolated_points])

        # A buffer of 4 means 4.0 meter for each side !!
        road_poly = road_spine.buffer(4.0, cap_style=2, join_style=2)
        road_patch = PolygonPatch(road_poly, fc='gray', ec='dimgray')  # ec='#555555', alpha=0.5, zorder=4)
        plt.gca().add_patch(road_patch)

        # Interpolated Points
        sx = [t[0] for t in interpolated_points]
        sy = [t[1] for t in interpolated_points]
        plt.plot(sx, sy, 'yellow')

        right_points = road_spine.parallel_offset(3.9, "right", resolution=16, join_style=1, mitre_limit=5.0)
        x, y = right_points.coords.xy
        plt.plot(x, y, 'white')
        # plt.plot(x, y, 'bo')

        left_points =  road_spine.parallel_offset(3.9, "left", resolution=16, join_style=1, mitre_limit=5.0)
        x, y = left_points.coords.xy
        plt.plot(x, y, 'white')
        # plt.plot(x, y, 'bo')

        # Road Points
        x = [t[0] for t in road.nodes]
        y = [t[1] for t in road.nodes]
        plt.plot(x, y, 'wo')

        # Plot the little triangle indicating the starting position of the ego-vehicle
        # delta_x = sx[1] - sx[0]
        # delta_y = sy[1] - sy[0]

        # current_angle = atan2(delta_y, delta_x)
        #
        # rotation_angle = degrees(current_angle)
        # transformed_fov = rotate(self.little_triangle, origin=(0, 0), angle=rotation_angle)
        # transformed_fov = translate(transformed_fov, xoff=sx[0], yoff=sy[0])
        # plt.plot(*transformed_fov.exterior.xy, color='black')
        #
        # Plot the little square indicating the ending position of the ego-vehicle
        # delta_x = sx[-1] - sx[-2]
        # delta_y = sy[-1] - sy[-2]
        #
        # current_angle = atan2(delta_y, delta_x)
        #
        # rotation_angle = degrees(current_angle)
        # transformed_fov = rotate(self.square, origin=(0, 0), angle=rotation_angle)
        # transformed_fov = translate(transformed_fov, xoff=sx[-1], yoff=sy[-1])
        # plt.plot(*transformed_fov.exterior.xy, color='black')
        #
        # Add information about the test validity
        # title_string = ""
        # if the_test.is_valid is not None:
        #     title_string = " ".join(
        #         [title_string, "Test", str(the_test.id), "is", ("valid" if the_test.is_valid else "invalid")])
        #     if not the_test.is_valid:
        #         title_string = title_string + ":" + the_test.validation_message
        #
        # plt.suptitle(title_string, fontsize=14)
        # plt.draw()
        # plt.pause(0.001)



if __name__ == "__main__":
    road = Road('road_rubber_sticky', rid='road_1')

    road_nodes = generate_road_nodes()
    # road_nodes = [
    #     (0, 30, 0, 8),
    #     (20, 30, 0, 8),
    #     (40, 30, 0, 8),
    #     (60, 30, 0, 8)
    # ]
    road.nodes.extend(road_nodes)
    road_visualizer = RoadVisualizer()
    road_visualizer.visualize_road(road)
    plt.show()

    road_spine = LineString([(rn[0],rn[1]) for rn in road_nodes])

    # The central marking is a road 10cm wide
    # central_marking_nodes = [(rn[0],rn[1], 0, 0.1) for rn in road_nodes]
    # print("Central Nodes", len(central_marking_nodes), central_marking_nodes)
    #
    # x, y = road_spine.parallel_offset(3.9, "right", resolution=16, join_style=1, mitre_limit=5.0).coords.xy
    # right_marking_nodes = [(p[0], p[1], 0, 0.1) for p in zip(x, y)]
    # # plt.plot(x, y, 'og')
    #
    # interpolated_points = common.interpolate([(p[0], p[1]) for p in right_marking_nodes], sampling_unit=10)
    # x = [p[0] for p in interpolated_points ]
    # y = [p[1] for p in interpolated_points ]
    # plt.plot(x, y, 'og')
    #
    # x, y = road_spine.parallel_offset(3.9, "left", resolution=16, join_style=1, mitre_limit=5.0).simplify(tolerance=5.0).coords.xy
    # left_marking_nodes = [(p[0], p[1], 0, 0.1) for p in zip(x, y)]
    # plt.plot(x, y, 'ob')
    # plt.show()

