### Setup the scenario
from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Camera
from shapely.geometry import Point
from shapely.affinity import translate
from matplotlib import pyplot as plt
from time import sleep
import numpy as np
from scipy.spatial.transform import Rotation as R

# Specify where BeamNG home and user are
BNG_HOME = "C:\\BeamNG.tech.v0.21.3.0"
BNG_USER = "C:\\BeamNG.tech_userpath"


def generate_trajectory():
    trajectory = [{
        "x": -74.834,
        "y": -2.0,
        "z": 0,
        "t": 0.9298799999999995
        },
        {
            "x": -18.013,
            "y": -2.0,
            "z": 0,
            "t": 11.15766
        },
        {
            "x": -12.856,
            "y": -2.273,
            "z": 0,
            "t": 12.087219770644147
        },
        {
            "x": -7.758,
            "y": -3.093,
            "z": 0,
            "t": 13.01665450724484
        },
        {
            "x": -2.775,
            "y": -4.45,
            "z": 0,
            "t": 13.946258891485794
        },
        {
            "x": 2.033,
            "y": -6.333,
            "z": 0,
            "t": 14.875703197079195
        },
        {
            "x": 6.703,
            "y": -8.542,
            "z": 0,
            "t": 15.805601054050594
        },
        {
            "x": 29.909,
            "y": -19.861,
            "z": 0,
            "t": 20.453954863490104
        }
    ]
    return trajectory

scenario = Scenario('tig', 'test_scenario')
# Ground level in TIG level
ground_level = -28.0
# Road
road_nodes = [
    (-100, 0, ground_level, 8),
    (  0, 0, ground_level, 8),
    (+100, 0, ground_level, 8)
]
road = Road('tig_road_rubber_sticky', rid='straight_road')
road.nodes.extend(road_nodes)
scenario.add_road(road)

# {
    #                 "x": -80.0,
    #                 "y": -2.0,
    #                 "z": 0,
    #                 "t": 0
    #             },

# Position the ego-car at the beginning of the road
# Hardcoded coordinates
direction_of_the_road = (0, 0, 1, -1)

# Place the ego-car at the beginning of the road, in the middle of the right lane
ego_position = (-80.0, -2.0, ground_level)
ego_vehicle = Vehicle('ego', model='etk800', licence='ego', color="white")
scenario.add_vehicle(ego_vehicle, pos=ego_position, rot=None, rot_quat=direction_of_the_road)

# Place a parked car on the right side of the road
parked_car_position = (0.0, -6.0, ground_level)
parked_vehicle = Vehicle('parked', model='etk800', licence='parked', color="red")
scenario.add_vehicle(parked_vehicle, pos=parked_car_position, rot=None, rot_quat=direction_of_the_road)

### Setup the cameras on the ego-vehicle
ego_cam_pos = (-0.3, 1.7, 1.0)
ego_cam_dir = (0, 1, 0)
ego_cam_fov = 70
ego_cam_res = (512, 512)
ego_camera = Camera(ego_cam_pos, ego_cam_dir, ego_cam_fov, ego_cam_res, colour=True, annotation=True, instance=True)
ego_vehicle.attach_sensor('ego_camera', ego_camera)

### Setup the cameras on the scenario. On top of parked car,
bird_cam_pos = (-10.0, -2.0, 10.0)
bird_cam_dir = (0, 0, -1)
bird_cam_fov = 60
bird_cam_res = (512, 512)
bird_view_camera = Camera(bird_cam_pos, bird_cam_dir, bird_cam_fov, bird_cam_res, colour=True)
scenario.add_camera(bird_view_camera, 'bird_view')

# 10 steps per second
TIMEOUT = 10 * 25 #secs

from tempfile import mkdtemp
import os

output_folder = mkdtemp()
print("Storing OUTPUT to ", output_folder)

def store_images(camera_name, frame_id, image_color, image_annotation):
    # Convert images to arrays
    array_color = np.asarray(image_color.convert('RGB'))
    array_annotation = np.asarray(image_annotation.convert('RGB'))
    # Store the arrays into target folder using camera_name and frame_id as identifiers

    output_file_color = os.path.join(
            output_folder,
            "_".join([camera_name, str(frame_id), "color"])+".npy"
            )
    with open(output_file_color, 'wb') as f:
        np.save(f, array_color)

    output_file_annotation = os.path.join(
        output_folder,
        "_".join([camera_name, str(frame_id), "annotation"])+".npy"
    )

    with open(output_file_annotation, 'wb') as f:
        np.save(f, array_annotation)

    if frame_id % 10 == 0:
        # Store the images as JPEG
        output_file_color = os.path.join(
            output_folder,
            "_".join([camera_name, str(frame_id), "color"]) + ".jpeg"
        )
        plt.imsave(output_file_color, array_color)

        output_file_annotation = os.path.join(
            output_folder,
            "_".join([camera_name, str(frame_id), "annotation"]) + ".jpeg"
        )
        plt.imsave(output_file_annotation, array_annotation)

        print("Stored to", output_file_color, output_file_annotation)

PLOT = False

with BeamNGpy('localhost', 64256, home=BNG_HOME, user=BNG_USER) as bng:

    scenario.make(bng)

    # Configure simulation
    bng.set_deterministic()
    bng.set_steps_per_second(60)

    # Load the scenario and pause
    bng.load_scenario(scenario)
    bng.start_scenario()
    bng.pause()

    # Focus on Ego Car
    bng.switch_vehicle(ego_vehicle)

    # Configure the movement of the NPC vehicle
    ego_vehicle.ai_set_mode('disabled')
    ego_vehicle.ai_set_script(generate_trajectory())

    if PLOT:
        plt.ion()
        figure, axarr = plt.subplots(1, 3, figsize=(15, 5))
        # setting title
        plt.gca().set_aspect('equal', 'datalim')

    ego_camera_plot = None
    bird_view_camera_plot = None

    # Execute the simulation for one second, check the oracles and resume, until either the oracles or the timeout
    # trigger
    for frame_id in range(1, TIMEOUT):
        print("frame", frame_id)
        # Move one tenth of sec
        bng.step(6)

        # Refresh sensors
        # print(">> polling sensors from CAR")
        ego_vehicle.poll_sensors()
        bird_view_camera = scenario.render_cameras()['bird_view']

        # First round
        if ego_camera_plot is None:
            ego_camera_image = ego_camera.data['colour']
            ego_camera_image_annotation = ego_camera.data['annotation']

            bird_view_camera_image = bird_view_camera['colour']
            bird_view_camera_annotation = bird_view_camera['annotation']

            store_images('ego_camera', frame_id, ego_camera_image, ego_camera_image_annotation)
            store_images('bird_view', frame_id, bird_view_camera_image, bird_view_camera_annotation)

            # Refresh UI
            if PLOT:
                ego_camera_plot = axarr[0].imshow(np.asarray(ego_camera_image.convert('RGB')))
                bird_view_camera_plot = axarr[1].imshow(np.asarray(bird_view_camera_image.convert('RGB')))

                figure.canvas.draw()
                figure.canvas.flush_events()

                plt.draw()
                plt.pause(0.001)
        else:
            ego_camera_image = ego_camera.data['colour']
            ego_camera_image_annotation = ego_camera.data['annotation']

            bird_view_camera_image = bird_view_camera['colour']
            bird_view_camera_annotation = bird_view_camera['annotation']

            store_images('ego_camera', frame_id, ego_camera_image, ego_camera_image_annotation)
            store_images('bird_view', frame_id, bird_view_camera_image, bird_view_camera_annotation)

            # Refresh UI
            if PLOT:
                ego_camera_plot.set_data(np.asarray(ego_camera_image.convert('RGB')))
                bird_view_camera_plot.set_data(np.asarray(bird_view_camera_image.convert('RGB')))

                figure.canvas.draw()
                figure.canvas.flush_events()

                plt.draw()
                plt.pause(0.001)