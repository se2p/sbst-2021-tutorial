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

with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:
    scenario = Scenario('Utah', 'tod_test')
    scenario.make(bng)

    bng.load_scenario(scenario)
    bng.start_scenario()

    # Sets the current time of day. The time of day value is given as a float
    #         between 0 and 1. How this value affects the lighting of the scene is
    #         dependant on the map's TimeOfDay object.

    for i in range(0, 10):
        bng.set_tod(i * 0.1)
        input('Press enter when done...')
