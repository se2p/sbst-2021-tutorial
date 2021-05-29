# Create roads from a fixed amount of segments

# TODO Still open to finish: missing OBE monitor, distance to spine, maybe ranking by time and distance_to_obe ?

from numpy.random import randint
from numpy.random import rand

from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Damage, State, Timer

from test_oracles import TargetAreaOracle, SimpleOBEOracle
from trajectory_generator import generate_trajectory
from shapely.geometry import Point, LineString
from visualization import RoadVisualizer

import matplotlib.pyplot as plt

# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

SEGMENT_COUNT = 5

MIN_LENGTH = 5
MAX_LENGTH = 50

MIN_RADIUS = 10
MAX_RADIUS = 50

MIN_ANGLE = 10
MAX_ANGLE = 90

SPEED_LIMIT_KMH = 70.0

LANE_WIDTH = 4.0

GROUND_LEVEL = -28

ROAD_STARTING_POINT = Point(0, 0)
ROAD_STARTING_DIRECTION = 0

# Middle of the rigth lane
CAR_STARTING_POSITION = (LANE_WIDTH * 0.5, 5.0, GROUND_LEVEL)
CAR_STARTING_ROT = (0, 0, 1, 0)

# Roads should not be that long!
TIMEOUT = 120

global_test_count = 0


def generate_random_road(n_segments):
    individual = []
    for i in range(1, n_segments):
        individual.append(generate_random_road_segment())
    return individual


def generate_random_road_segment():
    if rand() <= 0.3:
        return {'trajectory_segments':
                    [{'type': 'straight', 'length': randint(MIN_LENGTH, MAX_LENGTH)}]
                }
    elif rand() <= 0.5:
        return {'trajectory_segments':
                    [{'type': 'turn', 'angle': - randint(MIN_ANGLE, MAX_ANGLE),
                      'radius': randint(MIN_RADIUS, MAX_RADIUS)}]
                }
    else:
        return {'trajectory_segments':
                    [{'type': 'turn', 'angle': + randint(MIN_ANGLE, MAX_ANGLE),
                      'radius': randint(MIN_RADIUS, MAX_RADIUS)}]
                }


def replace_segment_mutation(road_segment):
    road_segment['trajectory_segments'] = generate_random_road_segment()['trajectory_segments']


def change_attribute_mutation(road_segment):
    if road_segment['trajectory_segments'][0]['type'] == 'straight':
        road_segment['trajectory_segments'][0]['length'] = randint(MIN_LENGTH, MAX_LENGTH)
    elif rand() <= 0.5:
        sign = 1.0 if (rand() <= 0.5) else -1.0
        road_segment['trajectory_segments'][0]['angle'] = randint(MIN_ANGLE, MAX_ANGLE) * sign
    else:
        road_segment['trajectory_segments'][0]['radius'] = randint(MIN_RADIUS, MAX_RADIUS)


def mutate(individual):
    # Clone the individual
    mutant = [dict(road_segment) for road_segment in individual]

    # Pick the road_segments to mutate
    for road_segment in individual:
        if rand() <= 1 / len(individual):
            if rand() <= 0.5:
                replace_segment_mutation(road_segment)
            else:
                change_attribute_mutation(road_segment)

    # print("Mutated Road", mutant)

    return mutant


def execute_experiment(individual, road_visualizer=None):
    global global_test_count
    global_test_count = global_test_count + 1

    # Create the scenario. Each test gets its own scenario
    scenario = Scenario('tig', "pcg_test_" + str(global_test_count))

    # All the roads start from the same place with the same initial straight segment
    wrapped_individual = [{'trajectory_segments':
                               [{'type': 'straight', 'length': 10}]
                           }]
    wrapped_individual.extend(individual)

    road_nodes = [(p[0], p[1], GROUND_LEVEL, 2 * LANE_WIDTH) for p in
                  generate_trajectory(ROAD_STARTING_POINT, ROAD_STARTING_DIRECTION, wrapped_individual)]

    road = Road('tig_road_rubber_sticky', rid='the_road')
    road.nodes.extend(road_nodes)
    scenario.add_road(road)

    if road_visualizer is not None:
        road_visualizer.visualize_road(road)

    ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="red")
    scenario.add_vehicle(ego_vehicle, pos=CAR_STARTING_POSITION, rot=None, rot_quat=CAR_STARTING_ROT)

    # Configure ego-car sensors
    state_sensor = State()
    ego_vehicle.attach_sensor('state', state_sensor)

    # Configure the ego-car destination
    destination = road_nodes[-1]
    scenario.add_checkpoints([destination], [(1.0, 1.0, 1.0)], ids=["goal_wp"])

    # Configure Oracle
    target_position = (road_nodes[-2][0], road_nodes[-2][1], road_nodes[-2][2])
    radius = 2.0 * LANE_WIDTH + 0.2
    target_area_reached_oracle = TargetAreaOracle(target_position, radius, state_sensor)

    # Connect to the running BeamNG
    bng = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
    try:
        bng.open(launch=False, deploy=False)
        scenario.make(bng)

        # Configure simulation
        bng.set_deterministic()
        bng.set_steps_per_second(60)

        # Load the scenario and pause
        bng.load_scenario(scenario)
        bng.start_scenario()
        bng.pause()

        # Focus the main camera on the ego_vehicle
        bng.switch_vehicle(ego_vehicle)

        road_edges = bng.get_road_edges('the_road')
        road_nodes = [(edges['middle'][0], edges['middle'][1], GROUND_LEVEL, 2 * LANE_WIDTH) for edges in road_edges]

        right_lane_center_polyline = LineString([(p[0], p[1], p[2]) for p in road_nodes]).parallel_offset(
            LANE_WIDTH * 0.5, "right")
        # , resolution=16, join_style=1, mitre_limit=5.0)

        # Setup the test Oracles
        simple_obe_monitor = SimpleOBEOracle(road_nodes, state_sensor)

        ego_vehicle.ai_drive_in_lane(True)
        ego_vehicle.ai_set_speed(SPEED_LIMIT_KMH / 3.6, mode='limit')
        ego_vehicle.ai_set_waypoint("goal_wp")

        # Execute the simulation for one second, check the oracles and resume, until either the oracles or the timeout
        # trigger
        distances = []

        for i in range(1, TIMEOUT):
            bng.step(30)

            # Poll data
            ego_vehicle.poll_sensors()

            distance = right_lane_center_polyline.distance(Point(state_sensor.data['pos']))
            distances.append(distance)
            # print("Distance to center of right lane", distance)

            # Check the oracles
            if simple_obe_monitor.check():
                # print("Test Failed!")
                return "Fail", max(distances)

            if target_area_reached_oracle.check():
                # print("Test Passed!")
                return "Pass", max(distances)

        # print("Test Failed with timeout!")
        return "Error", -1.0
    finally:
        bng.delete_scenario(scenario.path)
        bng.skt.close()


# tournament selection
def selection(pop, scores, k=3):
    # first random selection
    selection_ix = randint(len(pop))
    for ix in randint(0, len(pop), k - 1):
        # check if better (e.g. perform a tournament)
        if scores[ix] > scores[selection_ix]:
            selection_ix = ix
    return pop[selection_ix]

# https://machinelearningmastery.com/simple-genetic-algorithm-from-scratch-in-python/
def main():
    n_pop = 4
    n_iter = 10

    # initial population of random bitstring
    pop = [generate_random_road(5) for _ in range(n_pop)]

    print("Population size", len(pop))
    # keep track of best solution
    best, best_eval = None, 0

    # enumerate generations
    for gen in range(n_iter):
        # evaluate all candidates in the population
        executions = [execute_experiment(c) for c in pop]

        print("Results from the executions:")
        [ print(execution) for execution in executions ]
        # If we found a problem or there was an error the search is over
        test_outcome = [e[0] for e in executions]
        scores = [e[1] for e in executions]

        # check for new best solution
        for i in range(n_pop):
            if scores[i] > best_eval:
                best, best_eval = pop[i], scores[i]
                print("Generation: %d. New best score = %.3f" % (gen, scores[i]))

        # stop the search if we got what we wanted
        if "Fail" in test_outcome:
            print("Failed test. Search is over")
            return [best, best_eval]

        if "Error" in test_outcome:
            print("Error test. Search is over")
            return [best, best_eval]

        # select parents
        selected = [selection(pop, scores) for _ in range(n_pop)]

        # create the next generation
        children = list()
        for i in range(n_pop):
            # store for next generation
            children.append(mutate(selected[i]))

        # replace population
        pop = children

    print("Budget done. Search is over")
    return [best, best_eval]


if __name__ == "__main__":
    # This is the "main" Bng Client that starts and stop the simulator
    with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
        main()
