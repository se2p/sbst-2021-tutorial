import unittest
import common
from multiprocessing import Pool

from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Timer, State, Electrics, Damage, GForces
from beamngpy import ProceduralCone, ProceduralBump, ProceduralCube

from beamngpy import StaticObject

from shapely.geometry import Point, LineString, Polygon
from shapely.affinity import translate, rotate

from time import sleep
# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

class TargetAreaOracle():

    def __init__(self, target_position, radius, state_sensor):
        self.targer_position = Point(target_position)
        self.radius = radius
        self.state_sensor = state_sensor

    def check(self):
        distance_to_goal = self.targer_position.distance(Point(self.state_sensor.data['pos']))
        print("Distance to goal", distance_to_goal)
        return distance_to_goal < self.radius


class DamagedOracle():
    def __init__(self, damage_sensor):
        self.damage_sensor = damage_sensor

    def check(self):
        print("Damaged components:", self.damage_sensor.data['part_damage'])
        return len(self.damage_sensor.data['part_damage']) > 0


def runtime_monitor(vehicle_id, target_position, radius):
    bng = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
    bng = bng.open(launch=False, deploy=False)
    try:
        active_vehicles = bng.get_current_vehicles()
        vehicle = active_vehicles[vehicle_id]
        # Define the sensors
        timer = Timer()
        vehicle.attach_sensor('timer', timer)
        # Get current position and velocity via State
        state = State()
        vehicle.attach_sensor('state', state)
        target_position_reached = TargetAreaOracle(target_position, radius, state)
        # Report damaged components via Damage
        damage = Damage()
        vehicle.attach_sensor('damage', damage)
        has_crashed = DamagedOracle(damage)

        # Make sure the bng client also connects to the vehicle VM
        vehicle.connect(bng)

        while True:
            sleep(1)
            # Poll
            vehicle.poll_sensors()
            # Print
            if has_crashed.check():
                print("Car has damaged components")
                return (False, "Car has damaged components")

            if target_position_reached.check():
                print("Target Position Reached")
                return (True, "Target Position Reached")

    except Exception as e:
        print("Exception insider runtime monitor", e)
    finally:
        if bng:
            bng.skt.close()


class PassTestException(Exception):
    pass


TIMEOUT = 30

class RuntimeMonitoringTest(unittest.TestCase):

    def setUp(self):
        """
            Setup a basic scenario on the tig map with a straight two-lane road segment with lane markings embedded in
            its material's texture. Place the ego-car at the beginning of the road on the right lane
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

        # Ground level in TIG level
        ground_level = -28.0

        # Hardcoded coordinates
        start_of_the_road = Point(0, 30, ground_level)
        direction_of_the_road = (0, 0, 1, -1)
        lane_width = 4.0
        length_car = 5.0  # approx

        # Place a barriers in the middle of the lane
        barrier_position = translate(start_of_the_road, +30.0, -lane_width * 0.5, 0.01)
        barrier = StaticObject(name='barrier',
                                 pos=(barrier_position.x, barrier_position.y, barrier_position.z),
                                 rot=None,
                                 rot_quat=direction_of_the_road,
                                 scale=(1, 1, 1),
                                 shape='/levels/west_coast_usa/art/shapes/race/concrete_road_barrier_a.dae')

        self.scenario.add_object(barrier)

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(start_of_the_road, 0.0, -lane_width * 0.5)
        ego_position = translate(ego_position, length_car, 0.0)
        #
        self.ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
        self.scenario.add_vehicle(self.ego_vehicle, pos=(ego_position.x, ego_position.y, ground_level), rot=None,
                                  rot_quat=direction_of_the_road)

        # Add some debug information (visible only on developer's GUI)


    def test_monitor_ego_car_main_from_main_process(self):
        """
            Example of sensor usage to collect data for implementing standard oracles, both positive and negative
        """
        # Report the (simulation) time elapsed
        timer = Timer()
        self.ego_vehicle.attach_sensor('timer', timer)

        # Get current position and velocity via State
        state_sensor = State()
        self.ego_vehicle.attach_sensor('state', state_sensor)
        lane_width = 4.0
        ground_level = -28
        target_position = (60, 30, ground_level)
        radius = 2 * lane_width + 0.2
        target_area_reached_oracle = TargetAreaOracle(target_position, radius, state_sensor)

        # Report current "wheelspeed" via Electrics
        electrics = Electrics()
        self.ego_vehicle.attach_sensor('electrics', electrics)

        # Report damaged components via Damage
        damage_sensor = Damage()
        self.ego_vehicle.attach_sensor('damage', damage_sensor)
        damage_oracle = DamagedOracle(damage_sensor)

        # Configure the sensors to monitor ego_car
        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            # Add some detailed
            bng.add_debug_spheres([target_position], [radius], [(1, 1, 1, 0.2)])

            self.scenario.make(bng)
            bng.load_scenario(self.scenario)
            bng.start_scenario()
            for i in range(1,TIMEOUT):
                # Wait
                sleep(11)
                # Poll
                self.ego_vehicle.poll_sensors()
                # Check Oracles
                if damage_oracle.check():
                    self.fail("Damaged Components")

                if target_area_reached_oracle.check():
                    print("Car reached target location")
                    return

    def test_monitor_ego_car_main_from_another_process(self):
        lane_width = 4.0
        target_position = (60, 30, 0)
        radius = 2*lane_width+0.2

        try:
            with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
                self.scenario.make(bng)
                bng.load_scenario(self.scenario)
                # Start the runtime monitor after the scenario starts
                pool = Pool()
                # We cannot use the callback here to trigger a test fail, because there are different threads involved
                oracle_result = pool.apply_async(runtime_monitor,
                                                 args=(self.ego_vehicle.vid, target_position, radius,))
                # Do not accept more work
                pool.close()

                # Start the actual execution
                bng.start_scenario()
                # Do other stuff, but remember to check if the any of the oracles triggered in the meanwhile
                for i in range(1,TIMEOUT):
                    sleep(1)
                    if oracle_result.ready():
                        print("Test finished")
                        is_pass, msg = oracle_result.get()

                        if is_pass:
                            return
                        else:
                            self.fail(msg)

                self.fail("Test did not finished within time")
        except PassTestException:
            print("Test passed!")

class SynchronousSimulationTest(unittest.TestCase):

    def setUp(self):
        """
            Setup a basic scenario on the tig map with a straight two-lane road segment with lane markings embedded in
            its material's texture. Place the ego-car at the beginning of the road on the right lane
        """
        self.scenario = Scenario('tig', 'test_scenario')

        road_nodes = [
            (0, 30, 0, 8),
            (60, 30, 0, 8),
            (120, 30, 0, 8)
        ]
        road = Road('tig_road_rubber_sticky', rid='road_1')
        road.nodes.extend(road_nodes)
        self.scenario.add_road(road)

        # Ground level in TIG level
        ground_level = -28.0

        # Hardcoded coordinates
        start_of_the_road = Point(0, 30, ground_level)
        direction_of_the_road = (0, 0, 1, -1)
        lane_width = 4.0
        length_car = 5.0  # approx

        # Place the ego-car at the beginning of the road, in the middle of the right lane
        ego_position = translate(start_of_the_road, 0.0, -lane_width * 0.5)
        ego_position = translate(ego_position, length_car, 0.0)
        self.ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="white")
        self.scenario.add_vehicle(self.ego_vehicle, pos=(ego_position.x, ego_position.y, ground_level), rot=None,
                                  rot_quat=direction_of_the_road)
        # Report the (simulation) time elapsed
        self.timer_sensor = Timer()
        self.ego_vehicle.attach_sensor('timer', self.timer_sensor)

        # Get current position and velocity via State
        self.state_sensor = State()
        self.ego_vehicle.attach_sensor('state', self.state_sensor)

        self.electrics_sensor = Electrics()
        self.ego_vehicle.attach_sensor('electrics', self.electrics_sensor)

        self.damage_sensors = Damage()
        self.ego_vehicle.attach_sensor('damage', self.damage_sensors)

        self.gforces_sensor = GForces()
        self.ego_vehicle.attach_sensor('gforces', self.gforces_sensor)

    def test_synch_simulation(self):

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            # 60 FPS
            bng.set_steps_per_second(60)
            bng.set_deterministic()

            self.scenario.make(bng)
            bng.load_scenario(self.scenario)
            bng.start_scenario()

            # Pause the simulation
            bng.pause()

            ele = self.electrics_sensor.data
            g_forces = self.gforces_sensor.data

            for i in range(1,10):
                # Progress it for 1/10 sec
                bng.step(60)
                # Get data from sensors
                self.ego_vehicle.poll_sensors()
                self.ego_vehicle.update_vehicle()
                st = self.ego_vehicle.state
                print(st)
                #
                # timer = self.timer_sensor.data['time']
                # damage = self.damage_sensors.data['damage']
                # pos= self.state_sensor.data['pos']
                # dir = self.state_sensor.data['dir']
                # vel=self.state_sensor.data['vel']
                # gforces=(g_forces.get('gx', None), g_forces.get('gy', None), g_forces.get('gz', None))
                # gforces2=(g_forces.get('gx2', None), g_forces.get('gy2', None), g_forces.get('gz2', None))
                # steering=ele.get('steering', None)
                # steering_input=ele.get('steering_input', None)
                # brake=ele.get('brake', None)
                # brake_input=ele.get('brake_input', None)
                # throttle=ele.get('throttle', None)
                # throttle_input=ele.get('throttle_input', None)
                # throttleFactor=ele.get('throttleFactor', None)
                # engineThrottle=ele.get('engineThrottle', None)
                # wheelspeed=ele.get('wheelspeed', None)


if __name__ == '__main__':
    unittest.main()
