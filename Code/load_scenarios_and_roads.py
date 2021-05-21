import unittest

from beamngpy import BeamNGpy, Scenario, Road
from shapely.geometry import Point, LineString

from trajectory_generator import generate_trajectory, generate_left_marking, generate_right_marking

# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

def generate_road_nodes():
    """
    Utility methods to create a road as sequences of road segments starting from an initial location and direction.
    """
    initial_location = Point(10, 10)
    initial_rotation = 0
    driving_actions = []
    driving_actions.append(
        {'name': 'follow',
         'trajectory_segments':
             [
                 {'type': 'straight', 'length': 20.0},
                 {'type': 'turn', 'angle': -90.0, 'radius': 40.0},
                 {'type': 'turn', 'angle': +20.0, 'radius': 100.0}
             ]
         }
    )
    driving_actions.append(
        {'name': 'follow',
         'trajectory_segments':
             [
                 {'type': 'straight', 'length': 40.0}
             ]
         }
    )
    trajectory_points = generate_trajectory(initial_location, initial_rotation, driving_actions, SAMPLING_UNIT=30)
    # BeamNG road nodes are (x,y,z) + road_width
    road_nodes = [(tp[0], tp[1], 0, 8.0) for tp in trajectory_points]
    return road_nodes



class LoadAnExistingMap(unittest.TestCase):

    def test_load_map(self):
        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            scenario = Scenario('Utah', 'ai_test')
            scenario.make(bng)
            bng.load_scenario(scenario)
            bng.start_scenario()
            input('Press enter when done...')

class ProceduralRoadGeneration(unittest.TestCase):

    def test_generate_road_plain_asphalt(self):
        # Straight segment
        road_nodes = [
            (0, 30, 0, 8),
            (20, 30, 0, 8),
            (40, 30, 0, 8),
            (60, 30, 0, 8)
        ]

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            scenario = Scenario('tig', 'test_scenario_1')
            # The material is plain asphalt
            road = Road('road_rubber_sticky', rid='road_1')
            road.nodes.extend(road_nodes)
            scenario.add_road(road)
            scenario.make(bng)

            bng.load_scenario(scenario)
            bng.start_scenario()
            input('Press enter when done...')

    def test_generate_road_with_lanemarking_embedded(self):

        road_nodes = generate_road_nodes()

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            scenario = Scenario('tig', 'test_scenario_2')
            # This material comes already with lane markings
            road = Road('tig_road_rubber_sticky', rid='road_1')
            road.nodes.extend(road_nodes)
            scenario.add_road(road)
            scenario.make(bng)

            bng.load_scenario(scenario)
            bng.start_scenario()
            input('Press enter when done...')

    def test_generate_road_with_lanemarking_as_decal(self):

        road_nodes = generate_road_nodes()

        # We make the central marking 10cm wide
        central_marking_nodes = [(rn[0],rn[1], 0, 0.1) for rn in road_nodes]
        right_marking_nodes = generate_right_marking(road_nodes)
        left_marking_nodes = generate_left_marking(road_nodes)

        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
            scenario = Scenario('tig', 'test_scenario_3')
            # The road with lane markings is created by stacking decal roads on top of each other
            right_marking = Road('line_white', rid='right_white')
            right_marking.nodes.extend(right_marking_nodes)
            scenario.add_road(right_marking)

            left_marking = Road('line_white', rid='left_white')
            left_marking.nodes.extend(left_marking_nodes)
            scenario.add_road(left_marking)

            central_marking = Road('line_yellow', rid='central_yellow')
            central_marking.nodes.extend(central_marking_nodes)
            scenario.add_road(central_marking)

            road = Road('road_rubber_sticky', rid='road_1')
            road.nodes.extend(road_nodes)
            scenario.add_road(road)

            scenario.make(bng)

            bng.load_scenario(scenario)
            bng.start_scenario()
            input('Press enter when done...')

if __name__ == '__main__':
    unittest.main()
