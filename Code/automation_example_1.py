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
CAR_LENGTH = 5
INITIAL_DISTANCE = 15.0
INTER_NODE_DISTANCE = 20.0

def execute_experiment(individual):
    speeds = []
    for node_a, node_b in window(individual, 2):
        distance = Point(node_b['x'], node_b['y'], node_b['z']).distance(Point(node_a['x'], node_a['y'], node_a['z']))
        time = node_b['t'] - node_a['t']
        speed = distance / time * 3.6
        speeds.append(speed)

    print("Individual", [n['t'] for n in individual])
    print("Speed profile", speeds)


    coordinates = []
    radii = []
    rgba_colors = []

    for node in individual:
        coordinates.append([node['x'], node['y'], node['z'] + 1.0])
        radii.append(0.2)
        rgba_colors.append([1.0, 1.0, 1.0, 0.8])

    ground_level = -28.0

    # Hardcoded coordinates
    start_of_the_road = Point(0, 30, ground_level)
    direction_of_the_road = (0, 0, 1, -1)
    opposite_direction_of_the_road = (0, 0, 1, 1)
    lane_width = 4.0
    length_car = 5.0  # approx

    scenario = Scenario('tig', 'automated_1')

    road_nodes = [(INTER_NODE_DISTANCE * i, 30, ground_level, 8.0) for i in range(0,10)]
    road = Road('tig_road_rubber_sticky', rid='road')
    road.nodes.extend(road_nodes)
    scenario.add_road(road)

    destination = road_nodes[-1]
    scenario.add_checkpoints([destination], [(1.0, 1.0, 1.0)], ids=["goal_wp"])


    # Place the ego-car at the beginning of the road, in the middle of the right lane
    ego_position = translate(start_of_the_road, 0.0, -lane_width * 0.5)
    # Move the car a inside the road
    ego_position = translate(ego_position, length_car, 0.0)
    ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
    scenario.add_vehicle(ego_vehicle, pos=(ego_position.x, ego_position.y, ground_level), rot=None,
                              rot_quat=direction_of_the_road)

    # Create a vehicle in front of the ego-car, in same lane, following the same direction
    # # We use the current position of the ego-car
    heading_vehicle_position = translate(ego_position, INITIAL_DISTANCE, 0.0)
    heading_vehicle = Vehicle('heading', model='etk800', licence='heading', color="yellow")
    scenario.add_vehicle(heading_vehicle,
                              pos=(heading_vehicle_position.x, heading_vehicle_position.y, ground_level), rot=None,
                              rot_quat=direction_of_the_road)

    # Configure the sensors
    damage_sensor = Damage()
    ego_vehicle.attach_sensor('damage', damage_sensor)
    damage_oracle = DamagedOracle(damage_sensor)

    state_sensor = State()
    ego_vehicle.attach_sensor('state', state_sensor)
    target_position = (individual[-2]['x'], individual[-2]['y'], individual[-2]['z'])
    radius = 2.0 * LANE_WIDTH + 0.2
    target_area_reached_oracle = TargetAreaOracle(target_position, radius, state_sensor)

    # Show where the test should stop in red
    coordinates.append([c for c in target_position])
    radii.append(1.0)
    rgba_colors.append([1.0, 0.0, 0.0, 0.3])


    heading_vehicle_state_sensor = State()
    heading_vehicle.attach_sensor('state', heading_vehicle_state_sensor)

    # Configure the sensors
    heading_vehicle_damage_sensor = Damage()
    heading_vehicle.attach_sensor('damage', heading_vehicle_damage_sensor)
    heading_vehicle_damage_oracle = DamagedOracle(heading_vehicle_damage_sensor)

    with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
        scenario.make(bng)

        bng.add_debug_spheres(coordinates, radii, rgba_colors)

        # Focus the main camera on the ego_vehicle
        bng.set_deterministic()
        bng.set_steps_per_second(60)

        bng.load_scenario(scenario)
        bng.start_scenario()
        bng.pause()

        bng.switch_vehicle(ego_vehicle)
        # bng.switch_vehicle(heading_vehicle)

        # Configure the NPC
        heading_vehicle.ai_set_mode('disabled')
        heading_vehicle.ai_set_script(individual)

        # Configure Test Subject - After the scenario is started
        ego_vehicle.ai_drive_in_lane(True)
        ego_vehicle.ai_set_speed(SPEED_LIMIT_KMH / 3.6, mode='limit')
        ego_vehicle.ai_set_waypoint("goal_wp")

        distances = []

        for i in range(1, 60):
            bng.step(60)
            ego_vehicle.poll_sensors()
            heading_vehicle.poll_sensors()

            distance = Point(state_sensor.data['pos']).distance( Point(heading_vehicle_state_sensor.data['pos']))
            distances.append(distance)
            # print("Distance between vehicles", distance)

            if damage_oracle.check() or heading_vehicle_damage_oracle.check():
                print("Test Failed!")
                # Best value for Fitness
                return -1.0

            if target_area_reached_oracle.check():
                print("Test Passed!")
                return min(distances)

    print("Test Failed with timeout!")
    # Best value for Fitness
    return -2.0


# https://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator
def window(iterable, size):
    itrs = it.tee(iterable, size)
    shiftedStarts = [it.islice(anItr, s, None) for s, anItr in enumerate(itrs)]
    return zip(*shiftedStarts)

def mutate(individual):
    # Clone the original individual
    mutant = [dict(node) for node in individual]

    # Try to change the position on the road using Gaussian noise with prob X
    # Bound this to the lane?
    for index, node in enumerate(mutant):
        if random.random() <= 1 / len(node):
            delta = np.random.normal(0, LANE_WIDTH * 0.25, 1)[0]
            node['y'] = node['y'] + delta
            print("Mutating node", index, "position by", delta)
            # Hardcoded to avoid going too much out the lane (30-26)
            if node['y'] > 32:
                node['y'] = 30.0
            if node['y'] < 24:
                node['y'] = 26.0

    cumulative_delta = 0.0
    for index, node in enumerate(mutant):
        if random.random() <= 1 / len(node):
            delta = np.random.normal(0, 1.0, 1)[0]
            print("Mutating node", index, "inter-time by ", delta)

            if index > 0:
                # Inter-node time
                inter_node_time = node['t'] - mutant[index - 1]['t'] + delta
                predicted_speed = INTER_NODE_DISTANCE / inter_node_time * 3.6
                #
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

        # Move in the future or in the past this point, but keep the others as they are
        node['t'] = node['t'] + delta + cumulative_delta
        # We need to keep track of the cumulative time, as this is not "inter-node" time, but absolute!
        cumulative_delta = cumulative_delta + delta

    return mutant


def main():
    # Initial Individual -
    # - Ca 50km/h constant speed with 1.5
    # - Ca 36 km/h constant speed with 2.0
    # - Ca 29 km/h constant speed with 2.5
    best_individual = []

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
        # Check for improvement
        if distance < best_distance:
            best_distance = distance
            best_individual = new_individual
            print("Improved fitness to", best_distance)

        if distance < 0.0:
            print("Goal reached. Stop the search")
            break

    print("Final fitness", best_distance)

if __name__ == "__main__":
    main()
