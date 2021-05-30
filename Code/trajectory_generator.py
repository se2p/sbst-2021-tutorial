# This code comes from the SBST Tool competition
from numpy import linspace, array, cross, dot
from shapely.geometry import LineString, Point
from shapely.affinity import translate, rotate, scale
from scipy.spatial import geometric_slerp
from math import sin, cos, radians, degrees, atan2, copysign
import common

def generate_trajectory(initial_location, initial_rotation, driving_actions, SAMPLING_UNIT = 5):
        segments = []
        for driving_action in driving_actions:
            segments.extend(driving_action["trajectory_segments"])

        last_location = initial_location
        last_rotation = initial_rotation

        trajectory_points = [initial_location]
        len_coor = []

        for s in segments:
            # Generate the segment from the initial position and rotation
            # Then update the initial position and rotation for the next segment
            segment = None
            if s["type"] == 'straight':
                # Create an horizontal line of given length from the origin
                segment = LineString([(x, 0) for x in linspace(0, s["length"], 8)])
                # Rotate it
                segment = rotate(segment, last_rotation, (0, 0))
                # Move it
                segment = translate(segment, last_location.x, last_location.y)
                # Update last rotation and last location
                last_rotation = last_rotation  # Straight segments do not change the rotation
                last_location = Point(list(segment.coords)[-1])

            elif s["type"] == 'turn':
                # Generate the points over the circle with 1.0 radius
                # # Vector (0,1)
                # start = array([cos(radians(90.0)), sin(radians(90.0))])
                # # Compute this using the angle
                # end = array([cos(radians(90.0 - s["angle"])), sin(radians(90.0 - s["angle"]))])
                start = array([1, 0])

                # Make sure that positive is
                # TODO Pay attention to left/right positive/negative
                end = array([cos(radians(s["angle"])), sin(radians(s["angle"]))])
                # Interpolate over 8 points
                t_vals = linspace(0, 1, 8)
                result = geometric_slerp(start, end, t_vals)
                segment = LineString([Point(p[0], p[1]) for p in result])

                # Translate that back to origin
                segment = translate(segment, -1.0, 0.0)
                # Rotate
                if s["angle"] > 0:
                    segment = rotate(segment, -90.0, (0.0, 0.0), use_radians=False)
                else:
                    segment = rotate(segment, +90.0, (0.0, 0.0), use_radians=False)

                # Scale to radius on both x and y
                segment = scale(segment, s["radius"], s["radius"], 1.0, (0.0, 0.0))
                # Rotate it
                segment = rotate(segment, last_rotation, (0, 0))
                # Translate it
                segment = translate(segment, last_location.x, last_location.y)
                # Update last rotation and last location
                last_rotation = last_rotation + s["angle"]  # Straight segments do not change the rotation
                last_location = Point(list(segment.coords)[-1])

            if segment is not None:
                len_coor.append(len(list(segment.coords)))
                trajectory_points.extend([Point(x, y) for x, y in list(segment.coords)])

        the_trajectory = LineString(common.remove_duplicates([(p.x, p.y) for p in trajectory_points]))

        # Make sure we use as reference the NORTH
        the_trajectory = translate(the_trajectory, - initial_location.x, - initial_location.y)
        # Rotate by -90 deg
        the_trajectory = rotate(the_trajectory, +90.0, (0, 0))
        # Translate it back
        the_trajectory = translate(the_trajectory, + initial_location.x, + initial_location.y)

        # Interpolate and resample uniformly - Make sure no duplicates are there. Hopefully we do not change the order
        # TODO Sampling unit is 5 meters for the moment. Can be changed later
        interpolated_points = common.interpolate([(p[0], p[1]) for p in list(the_trajectory.coords)], sampling_unit = SAMPLING_UNIT)

        # Concat the speed to the point
        trajectory_points = list(the_trajectory.coords)
        start = 0
        sls = []
        sl_coor = []
        for s in len_coor:
            sl_coor.append([start, start + s])
            start = sl_coor[-1][1] - 1
        for s in sl_coor:
            sls.append(LineString(trajectory_points[s[0]:s[1]]))

        trajectory_points = []
        for line in sls:
            for p in interpolated_points:
                point = Point(p[0], p[1])
                if point.distance(line) < 0.5 and p not in trajectory_points:
                    trajectory_points.append((p[0], p[1]))

        # Return triplet
        return trajectory_points


def generate_left_marking(road_nodes):
    return _generate_lane_marking(road_nodes, "left")


def generate_right_marking(road_nodes):
    return _generate_lane_marking(road_nodes, "right")

def _generate_lane_marking(road_nodes, side):
    """
    BeamNG has troubles rendering/interpolating textures when nodes are too close to each other, so we need
    to resample them.
    To Generate Lane marking:
     1 Compute offset from the road spice (this creates points that are too close to each other to be interpolated by BeamNG)
     2 Reinterpolate those points using Cubic-splines
     3 Resample the spline at 10m distance
    """
    road_spine = LineString([(rn[0],rn[1]) for rn in road_nodes])
    x, y = road_spine.parallel_offset(3.9, side, resolution=16, join_style=1, mitre_limit=5.0).coords.xy
    interpolated_points = common.interpolate([(p[0], p[1]) for p in zip(x, y)], sampling_unit=10)
    return [(p[0], p[1], 0, 0.1) for p in interpolated_points]