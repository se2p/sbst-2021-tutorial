import unittest

from beamngpy import BeamNGpy
from time import sleep

# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

def do_the_sleep(for_seconds):
    print('Sleep for', for_seconds, 'seconds and stop')
    for i in reversed(range(1, for_seconds, )):
        print(i)
        sleep(1)


class StartFreshInstanceOfTheSimulator(unittest.TestCase):

    def test_that_simulation_start(self):
        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER):
            do_the_sleep(5)

    def test_that_simulation_restart(self):
        with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER):
            do_the_sleep(3)


class StartFreshInstanceOfTheSimulatorUsingSetupAndTearDown(unittest.TestCase):

    def setUp(self):
        self.beamng = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
        self.beamng = self.beamng.open(launch=True)

    def tearDown(self):
        if self.beamng:
            self.beamng.close()

    def test_that_simulation_start(self):
        do_the_sleep(5)

    def test_that_simulation_restart(self):
        do_the_sleep(3)


class SharedInstance(unittest.TestCase):
    # Static Field
    beamng = None

    @classmethod
    def setUpClass(cls):
        print("Starting the simulator.")
        bng = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
        cls.beamng = bng.open(launch=True)

    @classmethod
    def tearDownClass(cls):
        print("Tear down the simulator.")
        if cls.beamng:
            cls.beamng.close()

    def test_that_can_connect_to_simulator(self):
        print("Connecting to simulator")
        # This can also be externalized to setUp/tearDown methods
        client_a = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
        try:
            client_a.open(launch=False, deploy=False)
            do_the_sleep(2)
        finally:
            client_a.skt.close()

    def test_that_can_reconnect_to_simulator(self):
        print("Connecting to simulator (again)")
        client_b = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
        try:
            client_b.open(launch=False, deploy=False)
            do_the_sleep(5)
        finally:
            client_b.skt.close()


if __name__ == '__main__':
    unittest.main()
