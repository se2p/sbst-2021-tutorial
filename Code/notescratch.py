import unittest
import common

from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Timer, Camera
from beamngpy import ProceduralCone, ProceduralBump, ProceduralCube

from beamngpy import StaticObject

from shapely.geometry import Point, LineString
from shapely.affinity import translate, rotate
from math import radians
from trajectory_generator import generate_trajectory, generate_left_marking, generate_right_marking

# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"


class PlaceVehiclesAndObstacles(unittest.TestCase):

    def setUp(self):
        """
            Setup a basic scenario on the tig map with a straight two-lane road segment with lane markings embedded in
            its material's texture
        """
        self.scenario = Scenario('tig', 'test_scenario')

        road_nodes = [
            (0, 30, 0, 8),
            (60, 30, 0, 8),
            (120, 30, 0, 8)
        ]
        road = Road('tig_road_rubber_sticky', rid='road_1' )
        road.nodes.extend(road_nodes)
        self.scenario.add_road(road)

    def test_generate_ground_and_flying_vehicles(self):
        """
        Adding a vehicle in the wrong place, i.e., mid-air, will cause it to fall and break
        :return:
        """
        # Setup

        # Create a vehicle and put it on the ground, ground is at -28.0 in tig level
        ground_vehicle = Vehicle('ground_vehicle', model='etk800', licence='ground', color="red")
        self.scenario.add_vehicle(ground_vehicle, pos=(0, 0, -28.0), rot=None, rot_quat=(0, 0, 1, 0))

        # Create a vehicle at 0, so 28.0 meters above the tig ground level
        flying_vehicle = Vehicle('flying_vehicle', model='etk800', licence='flying', color="yellow")
        self.scenario.add_vehicle(flying_vehicle, pos=(0, 10, 0.0), rot=None, rot_quat=(0, 0, 1, 0))

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            self.scenario.make(bng)
            bng.load_scenario(self.scenario)
            bng.start_scenario()

            input('Press enter when done...')

    def test_place_vehicles_in_front_and_opposite_direction(self):
        ground_level = -28.0

        # Hardcoded coordinates
        start_of_the_road = Point(0, 30, ground_level)
        direction_of_the_road = (0, 0 , 1, -1)
        opposite_direction_of_the_road = (0, 0, 1, 1)
        lane_width = 4.0
        length_car = 5.0 # approx

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(start_of_the_road, 0.0, -lane_width*0.5)
        # Move the car a inside the road
        ego_position = translate(ego_position, length_car, 0.0)
        ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
        self.scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, ground_level), rot=None, rot_quat=direction_of_the_road)

        # Create a vehicle in front of the ego-car, in same lane, following the same direction
        # We use the current position of the ego-car
        heading_vehicle_position = translate(ego_position, +20.0, 0.0)
        heading_vehicle = Vehicle('heading', model='autobello', licence='heading', color="yellow")
        self.scenario.add_vehicle(heading_vehicle, pos=(heading_vehicle_position.x, heading_vehicle_position.y, ground_level), rot=None, rot_quat=direction_of_the_road)

        # Create a vehicle in front of the ego, on the opposite lane, following the opposite direction
        opposite_vehicle_position = translate(ego_position, +10.0, +lane_width)
        opposite_vehicle = Vehicle('opposite', model='citybus', licence='opposite', color="white")

        self.scenario.add_vehicle(opposite_vehicle, pos=(opposite_vehicle_position.x, opposite_vehicle_position.y, ground_level), rot=None, rot_quat=opposite_direction_of_the_road)

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            self.scenario.make(bng)
            bng.switch_vehicle(ego_vehicle)
            bng.load_scenario(self.scenario)
            bng.start_scenario()

            # Focus the main camera on the ego_vehicle
            

            # Debug information
            coordinates = []
            coordinates.extend([p for p in translate(ego_position, 0, 0, +2.5).coords])
            coordinates.extend([p for p in translate(heading_vehicle_position, 0, 0, +1.5).coords])
            coordinates.extend([p for p in translate(opposite_vehicle_position, 0, 0, +0.5).coords])
            #
            radii = [0.1, 0.1, 0.1]
            rgba_colors = [
                [1.0, 0.0, 0.0, 1.0], # red
                [1.0, 1.0, 0.0, 1.0], # yellow
                [1.0, 1.0, 1.0, 1.0] # white
            ]
            bng.add_debug_spheres(coordinates, radii, rgba_colors, cling=False, offset=0)

            print("scenario started")
            input('Press enter when done...')

    def test_place_procedurally_generated_obstacles(self):
        # Place procedurally generate cones (like the moose test)
        ground_level = -28.0

        # Hardcoded coordinates
        start_of_the_road = Point(0, 30, ground_level)
        direction_of_the_road = (0, 0, 1, -1)
        opposite_direction_of_the_road = (0, 0, 1, 1)
        lane_width = 4.0
        length_car = 5.0  # approx

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(start_of_the_road, 0.0, -lane_width * 0.5)
        # Move the car a inside the road
        ego_position = translate(ego_position, length_car, 0.0)
        ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
        self.scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, ego_position.z), rot=None,
                                  rot_quat=direction_of_the_road)

        # Place a bump 20m in front of the ego car
        # https://en.wikipedia.org/wiki/Speed_bump
        # A speed bump is a bump in a roadway with heights typically ranging between 76 and 102 millimetres.
        # The traverse distance of a speed bump is typically less than or near to 0.30 m (1 ft); contrasting with the
        # wider speed humps, which typically have a traverse distance of 3.0 to 4.3 m
        bump_position = translate(start_of_the_road, +20.0, 0.0)
        # TODO Adjust to it fits the entire road
        bump = ProceduralBump(name='bump',
                              pos=(bump_position.x, bump_position.y, bump_position.z),
                              rot=None,
                              rot_quat=(0, 0, 0, 1),
                              width=1.0,
                              length=2*(lane_width+0.1),
                              height=0.1,
                              upper_length= 2*(lane_width-0.1), # The size of the upper part
                              upper_width=0.4, # The size of the upper part,
                              material="bumber"
                              )
        self.scenario.add_procedural_mesh(bump)

        # THOSE ARE HARD OBSTACLES!
        # Create the moose test
        # Traffic cones are designed to be highly visible and easily movable. Various sizes are used, commonly ranging
        # from around 30 cm (11.8 in) to a little over 1 m (39.4 in). Traffic cones come in many different colors,
        # with orange, yellow, pink and red being the most common colors due to their brightness. Others come in green
        # and blue, and may also have a retroreflective strip (commonly known as "flash tape") to increase their
        # visibility.
        # 18/45.72 Inch Cone Dimensions: Reflective Height: 18 Inches.
        # Base Width: 10.50/26.67 Inches. Weight: 3.0 lbs.
        # 28/71.12 Inch Cone Dimensions: Reflective Height: 28 Inches.
        # Base Width: 14.00/35.56 Inches. Weight: 5 lbs, 7 lbs & 10 lbs.
        # 36/91.44 Inch Cone Dimensions: Refl ective Height: 36 Inches.
        # Base Width: 14/35.56 Inches. Weight: 10 lbs
        # material
        cone_position = translate(bump_position, +20.0, 0.0)
        cone = ProceduralCone(name='cone',
                              pos=(cone_position.x, cone_position.y, cone_position.z),
                              rot=None,
                              rot_quat=(0, 0, 0, 1),
                              radius=0.35,
                              height=1,
                              material='rumblestrip')
        self.scenario.add_procedural_mesh(cone)

        cone_position = translate(cone_position, +1.0, 0.0)
        cone = ProceduralCone(name='big_cone',
                              pos=(cone_position.x, cone_position.y, cone_position.z),
                              rot=None,
                              rot_quat=(0, 0, 0, 1),
                              radius=0.5,
                              height=2,
                              material='rumblestrip')
        self.scenario.add_procedural_mesh(cone)

        wall_position = translate(bump_position, +40.0, 0.0)
        wall = ProceduralCube(name='cube',
                              pos= (wall_position.x, wall_position.y, wall_position.z),
                              rot=None,
                              rot_quat=(0, 0, 0, 1),
                              size=(2*lane_width, 0.5, 4),
                              material='brickwall1')
        self.scenario.add_procedural_mesh(wall)

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            self.scenario.make(bng)

            bng.load_scenario(self.scenario)
            bng.start_scenario()

            # Focus the main camera on the ego_vehicle
            bng.switch_vehicle(ego_vehicle)
            input('Press enter when done...')

    def test_place_obstacles(self):
        # Place procedurally generate cones (like the moose test)
        ground_level = -28.0

        # Hardcoded coordinates
        start_of_the_road = Point(0, 30, ground_level)
        direction_of_the_road = (0, 0, 1, -1)
        facing_of_the_road = (0, 0, 0, 1)

        lane_width = 4.0
        length_car = 5.0  # approx

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(start_of_the_road, 0.0, -lane_width * 0.5)
        # Move the car a inside the road
        ego_position = translate(ego_position, length_car, 0.0)
        ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
        self.scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, ego_position.z), rot=None,
                                  rot_quat=direction_of_the_road)

        # Import a concrete barrier and place it on the side of the road. Since the barrier model is "frontal",
        # we need to rotate it a bit
        barrier_position = translate(start_of_the_road, +20.0, -lane_width, 0.01)
        barrier = StaticObject(name='barrier',
                               pos=(barrier_position.x, barrier_position.y, barrier_position.z),
                               rot=None,
                               rot_quat=facing_of_the_road,
                               scale=(1, 1, 1),
                               shape='/levels/west_coast_usa/art/shapes/race/concrete_road_barrier_a.dae')
        self.scenario.add_object(barrier)

        barrier_position = translate(start_of_the_road, +30.0, +lane_width*0.5, 0.01)
        barrier_1 = StaticObject(name='barrier_1',
                                 pos=(barrier_position.x, barrier_position.y, barrier_position.z),
                                 rot=None,
                                 rot_quat=direction_of_the_road,
                                 scale=(1, 1, 1),
                                 shape='/levels/west_coast_usa/art/shapes/race/concrete_road_barrier_a.dae')

        self.scenario.add_object(barrier_1)

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            self.scenario.make(bng)

            bng.load_scenario(self.scenario)
            bng.start_scenario()

            # Focus the main camera on the ego_vehicle
            bng.switch_vehicle(ego_vehicle)
            input('Press enter when done...')

    # def test_place_vehicles_on_steep_road(self):
    #     """
    #     Show the effect of clint=True by placing the car on a steep road inside an existing map
    #     """
    #     another_scenario = Scenario('Utah', 'test')
    #     ego = Vehicle('test_car', model='etk800')
    #     # The target position of the vehicle has been found by "free-roaming" the Utah map and using
    #     # the world editor
    #     pos = (814.88, -615.92, 147.55)
    #     # This value has been randomly
    #     rot = (0, 0, 1, 1)
    #     # Add the vehicle and make sure that no matter the valye o f
    #     another_scenario.add_vehicle(ego, pos=pos, rot=None, rot_quat=rot, cling=True)
    #
    #     ego = Vehicle('test_car', model='etk800')
    #     # The target position of the vehicle has been found by "free-roaming" the Utah map and using
    #     # the world editor
    #     pos = (814.88, -615.92, 147.55)
    #     # This value has been randomly
    #     rot = (0, 0, 1, 1)
    #     # Add the vehicle and make sure that no matter the valye o f
    #     another_scenario.add_vehicle(ego, pos=pos, rot=None, rot_quat=rot, cling=True)
    #
    #     with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
    #         another_scenario.make(bng)
    #         bng.load_scenario(another_scenario)
    #         bng.start_scenario()
    #         input('Press enter when done...')
    #
    # def load_a_scenario_and_move_furnt


if __name__ == '__main__':
    unittest.main()
