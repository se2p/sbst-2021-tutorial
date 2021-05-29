import unittest
from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import State, Damage, Camera, Timer
from trajectory_generator import generate_trajectory
from test_oracles import TargetAreaOracle, OBEOracle

from shapely.geometry import Point, LineString, Polygon
from shapely.affinity import translate, rotate

from multiprocessing import Process, Queue

from time import sleep
# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

GROUND_LEVEL = -28.0
LANE_WIDTH = 4.0
CAR_LENGTH = 5


def generate_road():
    direction_of_the_road = (0, 0, +180.0)

    # Generate a road using a sequence of segments
    initial_location = Point(10, 10, GROUND_LEVEL)
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
    return direction_of_the_road, [(tp[0], tp[1], GROUND_LEVEL, 8.0) for tp in road_spine]

def drive_with_nvidia(queue, vehicle_id, model_file):
    from self_driving import drive
    drive(queue, vehicle_id, model_file)


class InternalDrivingAI(unittest.TestCase):

    def test_beamng_ai(self):
        direction_of_the_road, road_nodes = generate_road()
        # This is the node at the beginning
        initial_location = (road_nodes[0][0], road_nodes[0][1], road_nodes[0][2])
        # This is the node at the end of the road
        destination = (road_nodes[-1][0], road_nodes[-1][1], road_nodes[-1][2])

        road = Road('tig_road_rubber_sticky', rid='road_1')
        road.nodes.extend(road_nodes)
        # If you want to see it,
        # road_visualizer = RoadVisualizer()
        # road_visualizer.visualize_road(road)

        # Create the scenario
        scenario = Scenario('tig', 'internal_driving_test')
        scenario.add_road(road)

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(initial_location, +LANE_WIDTH * 0.5, 0.0)
        ego_position = translate(ego_position, 0.0, CAR_LENGTH)
        ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
        scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, GROUND_LEVEL),
                             rot=direction_of_the_road, rot_quat=None)

        scenario.add_checkpoints([destination], [(1.0, 1.0, 1.0)], ids=["target_wp"])
        # Get current position and velocity via State
        state_sensor = State()
        ego_vehicle.attach_sensor('state', state_sensor)
        radius = 2 * LANE_WIDTH + 0.2
        # We place the target position for the test case just before the end of the road
        target_position = (road_nodes[-3][0], road_nodes[-3][1], road_nodes[-3][2])
        target_position_reached = TargetAreaOracle(target_position, radius, state_sensor)

        # Configure the sensors to monitor ego_car
        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            # Add some debug info
            bng.add_debug_spheres([target_position], [LANE_WIDTH], [(1, 1, 1, 0.2)])

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

class ExternalDrivingAI(unittest.TestCase):

    def test_driver_control_separate_process(self):

        # TODO This requires python 3.7 otherwise NVidia Driver will not work!

        direction_of_the_road, road_nodes = generate_road()
        # This is the node at the beginning
        initial_location = Point(road_nodes[0][0], road_nodes[0][1], road_nodes[0][2])
        # This is the node at the end of the road
        destination = (road_nodes[-1][0], road_nodes[-1][1], road_nodes[-1][2])

        road = Road('tig_road_rubber_sticky', rid='the_road')
        road.nodes.extend(road_nodes)

        scenario = Scenario('tig', 'external_driving_test')
        scenario.add_road(road)

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(initial_location, +LANE_WIDTH * 0.5, 0.0)
        ego_position = translate(ego_position, 0.0, CAR_LENGTH)
        ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
        scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, GROUND_LEVEL),
                             rot=direction_of_the_road, rot_quat=None)

        scenario.add_checkpoints([destination], [(1.0, 1.0, 1.0)], ids=["target_wp"])

        # Monitoring
        state_sensor = State()
        ego_vehicle.attach_sensor('state', state_sensor)
        # We place the target position for the test case just before the end of the road
        target_position = (road_nodes[-3][0], road_nodes[-3][1], road_nodes[-3][2])
        radius = 2 * LANE_WIDTH + 0.2
        target_position_reached = TargetAreaOracle(target_position, radius, state_sensor)

        timer_sensor = Timer()
        ego_vehicle.attach_sensor('timer', timer_sensor)

        # Configure the sensors to monitor ego_car
        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            # Add some debug info
            bng.add_debug_spheres([target_position], [LANE_WIDTH], [(1, 1, 1, 0.2)])

            scenario.make(bng)

            bng.load_scenario(scenario)
            bng.start_scenario()
            bng.pause()

            bng.switch_vehicle(ego_vehicle)

            # Start the driver Using another venv
            print("Starting driver")
            model_file = ".\\self-driving-car-178-2020.h5"
            queue = Queue()
            driver_process = Process(target=drive_with_nvidia, args=(queue, 'ego', model_file, ))
            driver_process.start()

            # Wait until the client started, max 30 sec
            print("Waiting for the driver to start...")
            queue.get()
            print("Ready...")
            # sleep(10)

            # road_geometry = bng.get_road_edges('the_road')
            # obe_oracle = OBEOracle(road_geometry, state_sensor)
            try:
                while True:
                    print("> Polling sensors")
                    ego_vehicle.poll_sensors()

                    # Use timer to filter out duplicate sensors
                    elapsed_time = timer_sensor.data['time']

                    if target_position_reached.check():
                        print("Car reached target location. Exit")
                        return

                    # if obe_oracle.check():
                    #     print("Car drove off lane")
                    #     self.fail("Car is out of the lane!")

                    # Ensure monitoring is faster than driver
                    sleep(1)
            except Exception as e:
                print("ERROR", e)
            finally:
                # Kill the driver
                if driver_process.is_alive():
                    driver_process.terminate()

if __name__ == '__main__':
    unittest.main()
