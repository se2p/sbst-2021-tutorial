import unittest
import common
from multiprocessing import Pool
from visualization import RoadVisualizer
from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Timer, State, Electrics, Damage
from trajectory_generator import generate_trajectory
from test_oracles import TargetAreaOracle

from shapely.geometry import Point, LineString, Polygon
from shapely.affinity import translate, rotate

from time import sleep
# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

class InternalDrivingAI(unittest.TestCase):

    def test_beamng_ai(self):
        ground_level = -28.0
        lane_width = 4.0
        length_car = 5
        direction_of_the_road = (0, 0, +180.0)

        # Generate a road using a sequence of segments
        initial_location = Point(10, 10, ground_level)
        initial_rotation = 0
        road_segments = []
        # Fixed. Ensure all the rotations are the same...
        road_segments.append(
            {
                'trajectory_segments':
                    [
                        {'type': 'straight', 'length': 10.0}
                    ]
            }
        )
        road_segments.append(
            {
             'trajectory_segments':
                 [
                     {'type': 'straight', 'length': 30.0},
                     {'type': 'turn', 'angle': -90.0, 'radius': 20.0},
                     {'type': 'turn', 'angle': -20.0, 'radius': 100.0}
                 ]
             }
        )
        road_segments.append(
            {
             'trajectory_segments':
                 [
                     {'type': 'straight', 'length': 4.0},
                     {'type': 'turn', 'angle': +45.0, 'radius': 12.0},
                     {'type': 'turn', 'angle': +45.0, 'radius': 24.0},
                     {'type': 'turn', 'angle': +45.0, 'radius': 48.0}
                 ]
             }
        )
        road_spine = generate_trajectory(initial_location, initial_rotation, road_segments, SAMPLING_UNIT=30)
        # BeamNG road nodes are (x,y,z) + road_width
        road_nodes = [(tp[0], tp[1], ground_level, 8.0) for tp in road_spine]

        # The node BEFORE the end of the road is the destination.
        destination = (road_nodes[-1][0], road_nodes[-1][1], road_nodes[-1][2])

        road = Road('tig_road_rubber_sticky', rid='road_1')
        road.nodes.extend(road_nodes)
        # road_visualizer = RoadVisualizer()
        # road_visualizer.visualize_road(road)

        # Create the scenario
        scenario = Scenario('tig', 'internal_driving_test')
        scenario.add_road(road)

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(initial_location, +lane_width * 0.5, 0.0)
        ego_position = translate(ego_position, 0.0, length_car)
        ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
        scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, ground_level), rot=direction_of_the_road,
                                  rot_quat=None)

        scenario.add_checkpoints([destination], [(1.0, 1.0, 1.0)], ids=["target_wp"])
        # # Report the (simulation) time elapsed
        # timer = Timer()
        # self.ego_vehicle.attach_sensor('timer', timer)
        #
        # Get current position and velocity via State
        state_sensor = State()
        ego_vehicle.attach_sensor('state', state_sensor)
        radius = 2 * lane_width + 0.2
        # Target position is a bit before the final destination
        target_position = (road_nodes[-3][0], road_nodes[-3][1], road_nodes[-3][2])
        target_position_reached = TargetAreaOracle(target_position, radius, state_sensor)

        #
        # # Report current "wheelspeed" via Electrics
        # electrics = Electrics()
        # self.ego_vehicle.attach_sensor('electrics', electrics)
        #
        # # Report damaged components via Damage
        # damage_sensor = Damage()
        # self.ego_vehicle.attach_sensor('damage', damage_sensor)
        # damage_oracle = DamagedOracle(damage_sensor)
        #
        # # Configure the sensors to monitor ego_car
        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            # Add some debug info
            bng.add_debug_spheres([target_position], [lane_width], [(1, 1, 1, 0.2)])

            bng.set_steps_per_second(60)
            bng.set_deterministic()

            scenario.make(bng)

            bng.load_scenario(scenario)
            bng.start_scenario()
            bng.pause()

            bng.switch_vehicle(ego_vehicle)
            ego_vehicle.ai_set_mode('manual')
            ego_vehicle.ai_set_waypoint('target_wp')
            ego_vehicle.ai_drive_in_lane('true')

            speed_limit = 50 / 3.6
            ego_vehicle.ai_set_speed(speed_limit, mode='limit')

            while True:
                bng.step(60)
                ego_vehicle.poll_sensors()

                # Check Oracles
                if target_position_reached.check():
                    print("Car reached target location. Exit")
                    return

    # def test_monitor_ego_car_main_from_another_process(self):
    #     lane_width = 4.0
    #     target_position = (60, 30, 0)
    #     radius = 2*lane_width+0.2
    #
    #     try:
    #         with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
    #             self.scenario.make(bng)
    #             bng.load_scenario(self.scenario)
    #             # Start the runtime monitor after the scenario starts
    #             pool = Pool()
    #             # We cannot use the callback here to trigger a test fail, because there are different threads involved
    #             oracle_result = pool.apply_async(runtime_monitor,
    #                                              args=(self.ego_vehicle.vid, target_position, radius,))
    #             # Do not accept more work
    #             pool.close()
    #
    #             # Start the actual execution
    #             bng.start_scenario()
    #             # Do other stuff, but remember to check if the any of the oracles triggered in the meanwhile
    #             for i in range(1,TIMEOUT):
    #                 sleep(1)
    #                 if oracle_result.ready():
    #                     print("Test finished")
    #                     is_pass, msg = oracle_result.get()
    #
    #                     if is_pass:
    #                         return
    #                     else:
    #                         self.fail(msg)
    #
    #             self.fail("Test did not finished within time")
    #     except PassTestExecption:
    #         print("Test passed!")

if __name__ == '__main__':
    unittest.main()
