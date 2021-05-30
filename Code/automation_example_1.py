# Test the ego-car car-following behavior by minimizing the distance between the ego-car and heading vehicle
# Individual: trajectory of NPC car (movement/speed)
# Mutation Operators:
    # MX: move trajectory points across the lane using Gaussian noise (capped)
    # MX: change inter-time between points using Gaussian noise (capped)

# Parameters: speed_limit
from ctypes import c_ubyte

from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Damage, State, Timer

from test_oracles import DamagedOracle, TargetAreaOracle

from shapely.geometry import Point
from shapely.affinity import translate

import numpy as np
import random
import itertools as it

# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

SPEED_LIMIT_KMH = 50
MIN_SPEED_LIMIT_KMH = 10

GROUND_LEVEL = -28.0
LANE_WIDTH = 4.0
CAR_LENGTH = 5.0
INITIAL_DISTANCE = 15.0
INTER_NODE_DISTANCE = 20.0

TIMEOUT = 60

global_test_count = 0


# https://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator
def window(iterable, size):
    itrs = it.tee(iterable, size)
    shiftedStarts = [it.islice(anItr, s, None) for s, anItr in enumerate(itrs)]
    return zip(*shiftedStarts)


def execute_experiment(individual):

    global global_test_count
    global_test_count = global_test_count + 1

    # Compute the speed profile. Mostly for debugging
    speeds = []
    for node_a, node_b in window(individual, 2):
        distance = Point(node_b['x'], node_b['y'], node_b['z']).distance(Point(node_a['x'], node_a['y'], node_a['z']))
        time = node_b['t'] - node_a['t']
        speed = distance / time * 3.6
        speeds.append(speed)
    print("Individual", global_test_count, [n['t'] for n in individual])
    print("Speed profile", speeds)

    # Debugging information
    coordinates = []
    radii = []
    rgba_colors = []

    for node in individual:
        coordinates.append([node['x'], node['y'], node['z'] + 1.0])
        radii.append(0.2)
        rgba_colors.append([1.0, 1.0, 1.0, 0.8])

    # Hardcoded initial positions
    start_of_the_road = Point(0, 30, GROUND_LEVEL)
    direction_of_the_road = (0, 0, 1, -1)

    # Create the scenario. Each test gets its own scenario
    scenario = Scenario('tig', "automated_test_"+str(global_test_count))

    # Nodes form a straight line, so the road is going to be a straight segment
    road_nodes = [(INTER_NODE_DISTANCE * i, 30, GROUND_LEVEL, 8.0) for i in range(0,10)]
    road = Road('tig_road_rubber_sticky', rid='road')
    road.nodes.extend(road_nodes)
    scenario.add_road(road)

    # Place the ego-car at the beginning of the road in the right lane
    ego_position = translate(start_of_the_road, 0.0, -LANE_WIDTH * 0.5)
    ego_position = translate(ego_position, CAR_LENGTH, 0.0)
    ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
    scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, GROUND_LEVEL), rot=None,
                              rot_quat=direction_of_the_road)

    # Configure ego-car sensors
    damage_sensor = Damage()
    ego_vehicle.attach_sensor('damage', damage_sensor)

    state_sensor = State()
    ego_vehicle.attach_sensor('state', state_sensor)

    # Create a vehicle in front of the ego-car, in same lane, following the same direction
    # This is the same as before: we have the INITIAL_DISTANCE fixed in this example
    heading_vehicle_position = translate(ego_position, INITIAL_DISTANCE, 0.0)
    heading_vehicle = Vehicle('heading', model='etk800', licence='heading', color="yellow")
    scenario.add_vehicle(heading_vehicle,
                              pos=(heading_vehicle_position.x, heading_vehicle_position.y, GROUND_LEVEL), rot=None,
                              rot_quat=direction_of_the_road)

    # Configure heading vehicle sensors
    heading_vehicle_damage_sensor = Damage()
    heading_vehicle.attach_sensor('damage', heading_vehicle_damage_sensor)

    heading_vehicle_state_sensor = State()
    heading_vehicle.attach_sensor('state', heading_vehicle_state_sensor)

    # Setup the test Oracles
    damage_oracle = DamagedOracle(damage_sensor)
    heading_vehicle_damage_oracle = DamagedOracle(heading_vehicle_damage_sensor)

    target_position = (individual[-2]['x'], individual[-2]['y'], individual[-2]['z'])
    radius = 2.0 * LANE_WIDTH + 0.2
    # Debug position where ends
    coordinates.append([c for c in target_position])
    radii.append(1.0)
    rgba_colors.append([1.0, 0.0, 0.0, 0.3])
    target_area_reached_oracle = TargetAreaOracle(target_position, radius, state_sensor)

    # Configure the ego-car destination. The end of the road
    destination = road_nodes[-1]
    scenario.add_checkpoints([destination], [(1.0, 1.0, 1.0)], ids=["goal_wp"])

    print("Connecting to simulator")
    # Connect to the running BeamNG
    bng = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
    try:
        bng.open(launch=False, deploy=False)
        scenario.make(bng)

        # Enable Debugging. Now we visualize small spheres that identify the trajectory
        # of the heading car
        bng.add_debug_spheres(coordinates, radii, rgba_colors)

        # Configure simulation
        bng.set_deterministic()
        bng.set_steps_per_second(60)

        # Load the scenario and pause
        bng.load_scenario(scenario)
        bng.start_scenario()
        bng.pause()

        # Focus the main camera on the ego_vehicle
        # bng.switch_vehicle(ego_vehicle)
        # We also focus the main camera on the heading_vehicle to see how
        # the "drunk" driver drives
        bng.switch_vehicle(heading_vehicle)

        # Configure the movement of the NPC vehicle
        heading_vehicle.ai_set_mode('disabled')
        heading_vehicle.ai_set_script(individual)

        # Configure the test subject
        ego_vehicle.ai_drive_in_lane(True)
        ego_vehicle.ai_set_speed(SPEED_LIMIT_KMH / 3.6, mode='limit')
        ego_vehicle.ai_set_waypoint("goal_wp")

        # Temporarily store runtime data to compute the fitness function
        distances = []

        # Execute the simulation for one second, check the oracles and resume, until either the oracles or the timeout
        # trigger
        for i in range(1, TIMEOUT):
            bng.step(60)

            # Poll data (for both vehicles!)
            ego_vehicle.poll_sensors()
            heading_vehicle.poll_sensors()

            # Compute our "fitness" function. We want to minimize the distance
            # between the two cars
            distance = Point(state_sensor.data['pos']).distance( Point(heading_vehicle_state_sensor.data['pos']))
            distances.append(distance)

            # Check the oracles
            if damage_oracle.check() or heading_vehicle_damage_oracle.check():
                print("Test Failed!")
                return -1.0

            if target_area_reached_oracle.check():
                print("Test Passed!")
                return min(distances)

        print("Test Failed with timeout!")
        return -2.0
    finally:
        bng.delete_scenario(scenario.path)
        bng.skt.close()


def mutate(individual):
    """
    Mutate a trajectory either by moving the nodes on the lateral axis (to make the heading vehicle swerve) or
    by changing the inter-time between node, hence, indirectly controlling the speed of the heading vehicle
    """

    # Clone the original individual
    mutant = [dict(node) for node in individual]

    # Change the position on the nodes with Gaussian noise
    for index, node in enumerate(mutant):
        if random.random() <= 1 / len(node):
            delta = np.random.normal(0, LANE_WIDTH * 0.25, 1)[0]
            node['y'] = node['y'] + delta
            print("Mutating node", index, "position by", delta)
            # Hardcoded to avoid going too much out the lane
            # Basically we cap the mutation
            if node['y'] > 34.0: # opposite lane
                node['y'] = 34.0
            if node['y'] < 24.0: # out of the road
                node['y'] = 24.0

    # We control the speed of the heading vehicle by changing the inter-time
    # between nodes. Again, we need to cap the mutation to avoid the heading car
    # to move back using the rear gear.
    cumulative_delta = 0.0
    for index, node in enumerate(mutant):
        if random.random() <= 1 / len(node):
            delta = np.random.normal(0, 1.0, 1)[0]
            print("Mutating node", index, "inter-time by ", delta)

            if index > 0:
                # Inter-node time
                inter_node_time = node['t'] - mutant[index - 1]['t'] + delta
                predicted_speed = INTER_NODE_DISTANCE / inter_node_time * 3.6
                # Try to recovery broken individuals. Avoid negative speeds and rear movements of the heading car
                if predicted_speed > SPEED_LIMIT_KMH:
                    print("Invalid delta. Too fast. Recomputing")
                    repair_intertime = INTER_NODE_DISTANCE / SPEED_LIMIT_KMH
                    # node['t'] =
                    # print("Invalid delta. Too fast.", predicted_speed, "Rejecting mutation")
                    delta = repair_intertime

                if predicted_speed < MIN_SPEED_LIMIT_KMH:
                    # print("Invalid delta. Too slow.", predicted_speed, "Rejecting mutation")
                    # delta = 0.0
                    # print("Invalid delta. Too slow. Recomputing")
                    repair_intertime = INTER_NODE_DISTANCE / MIN_SPEED_LIMIT_KMH
                    delta = repair_intertime
        else:
            delta = 0.0

        # Move in the future or in the past all the points to keep their original speed
        node['t'] = node['t'] + delta + cumulative_delta
        cumulative_delta = cumulative_delta + delta

    return mutant


def main():
    # - Ca 50km/h constant speed with 1.5
    # - Ca 36 km/h constant speed with 2.0
    # - Ca 29 km/h constant speed with 2.5
    best_individual = []

    # Create the initial default trajectory. It is a straight line, nodes are equidistant
    # and speed is more or less constant (time between node is the same)
    for i in range(0, 5):
        node = {
            'x': INTER_NODE_DISTANCE * i + INITIAL_DISTANCE,
            'y': 30 - LANE_WIDTH * 0.5,
            'z': GROUND_LEVEL + 1.0,
            't': 2.5 * i
        }
        best_individual.append(node)

    best_distance = execute_experiment(best_individual)
    print("Improved fitness to", best_distance)

    for generation in range(1,11):
        # Mutate best
        new_individual = mutate(best_individual)
        # Compute fitness
        distance = execute_experiment(new_individual)
        # Check for improvement. If the new individual is better we keep it, otherwise
        # we keep the old individual
        if distance < best_distance:
            best_distance = distance
            best_individual = new_individual
            print("Improved fitness to", best_distance)

        # If we make the cars crash, there's nothing more to search. So we can exit
        if distance < 0.0:
            print("Goal reached. Stop the search")
            break

    print("Final fitness", best_distance)

if __name__ == "__main__":
    # This is the "main" Bng Client that starts and stop the simulator
    # All the tests will share the same instance of the simulator
    with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
        main()
