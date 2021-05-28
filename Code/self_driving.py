import numpy as np

from udacity_utils import preprocess
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
from math import sqrt
from beamngpy import BeamNGpy
from beamngpy.sensors import Camera, State

# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"

class NvidiaPrediction:
    def __init__(self, model_file, speed_limit):
        self.MIN_SPEED = 5.0
        self.MAX_SPEED = speed_limit

        self.model = load_model(model_file)
        self.speed_limit = speed_limit

    def predict(self, image, speed_kmh):
        try:
            image = np.asarray(image)
            image = preprocess(image)
            image = np.array([image])

            steering_angle = float(self.model.predict(image, batch_size=1))

            if speed_kmh > self.speed_limit:
                self.speed_limit = self.MIN_SPEED  # slow down
            else:
                self.speed_limit = self.MAX_SPEED
            throttle = 1.0 - steering_angle ** 2 - (speed_kmh / self.speed_limit) ** 2
            return steering_angle, throttle

        except Exception as e:
            print(e)

# This run in a sub process
def drive(queue, vehicle_id, model_file):
    # Local import for the subprocess

    def compute_speed(vel_mps):
        return sqrt(sum([v**2 for v in vel_mps])) * 3.6

    print("Staring driver process")
    bng = BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER)
    bng = bng.open(launch=False, deploy=False)

    print("Configuring simulation steps")
    bng.set_steps_per_second(60)
    bng.set_deterministic()

    active_vehicles = bng.get_current_vehicles()
    vehicle = active_vehicles[vehicle_id]
    # Get current position and velocity via State
    state = State()
    vehicle.attach_sensor('state', state)
    # Show image
    # Create a vehicle with a camera sensor attached to it
    # Set up sensors

    cam_pos = (-0.3, 1.7, 1.0)
    cam_dir = (0, 1, 0)
    cam_fov = 120
    cam_res = (320, 160)

    camera = Camera(cam_pos, cam_dir, cam_fov, cam_res, colour=True)
    vehicle.attach_sensor('camera', camera)

    # Make sure the bng client also connects to the vehicle VM
    vehicle.connect(bng)
    print("Driver connected to vehicle")

    # to run GUI event loop
    plt.ion()
    # here we are creating sub plots
    figure, ax = plt.subplots(figsize=(5, 5))
    # setting title
    plt.gca().set_aspect('equal', 'datalim')
    # https://stackoverflow.com/questions/17835302/how-to-update-matplotlibs-imshow-window-interactively
    image = None
    frame_id = 0

    # We can notify the test case that we are ready
    queue.put('READY')

    predict = NvidiaPrediction(model_file, 30.0)

    while True:
        # Controller frequency: 1/10
        bng.step(6)
        frame_id += 1
        plt.title("Frame: " + str(frame_id), fontsize=10)
        # Poll
        vehicle.poll_sensors()
        # Show camera
        if image is None:
            image = camera.data['colour']
            aximage = ax.imshow(np.asarray(image.convert('RGB')))
        else:
            image = camera.data['colour']
            aximage.set_data(np.asarray(image.convert('RGB')))
            figure.canvas.flush_events()

        speed_kmh = compute_speed(state.data['vel'])
        print("Current speed Km/h", speed_kmh)

        steering_angle, throttle = predict.predict(image, speed_kmh)
        print("Controlling car with: Steering: ", steering_angle, "; Throttle: ", throttle)
        vehicle.control(throttle=throttle, steering=steering_angle, brake=0)