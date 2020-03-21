"""
A drone simulator for the AI class

author: Amy McGovern <dramymcgovern@gmail.com>
"""
import sys
# import os.path
# sys.path.append(
#     os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from droneSimulator import DroneSimulator, Drone, Velocity
from droneGUI import DroneGUI
import time
import threading
import numpy as np
import argparse

def user_drone_code(gui, drone, droneSimulator, num_timesteps):
    """
    This is where you put any of your user control code

    :param gui: link to the GUI so you know when the quit or pause button are pressed
    :param drone: the drone being controlled
    :param droneSimulator: the simulator for the drone
    :return:
    """

    # run until the quit button is pressed
    step = droneSimulator.get_timestep()
    while ((gui is not None and not gui.quit_pressed) or (gui is None and step < num_timesteps)):
        step = droneSimulator.get_timestep()
        if (step == 1):
            print("Takeoff")
            drone.takeoff()
            print("Done with takeoff")
        elif (step == 100):
            print("Flying forward")
            drone.forward_cm(100)
        elif (step == 300):
            print("Flying backward")
            drone.backward_cm(200)
        elif (step == 500):
            print("Flying right")
            drone.right_cm(100)
        elif (step == 700):
            print("Flying left")
            drone.left_cm(100)
        elif (step == 900):
            print("Flying up")
            drone.up_cm(30)
        elif (step == 1100):
            print("Flying down")
            drone.down_cm(30)
        elif (step == 1200):
            print("Landing")
            drone.land()
            print("Done with landing")

        # make sure you yield even for a fraction of a second in the user thread so that
        # the main simulator can run!
        time.sleep(0.01)

if __name__ == "__main__":
    room_length = 3
    room_width = 5
    room_height = 3
    num_mission_pads = 8
    num_obstacles = 3
    num_moving_obstacles = 1
    num_timesteps = 10000
    gui_pause = 0.01
    num_asteroids = num_mission_pads - num_obstacles
    marker_id_location_dict = {1: (0.5, 0), 2: (1.5, 0), 3: (2.5, 0),  # top
                               4: (3, 0.5), 5: (3, 1.5), 6: (3, 2.5), 7: (3, 3.5), 8: (3, 4.5),  # right
                               9: (2.5, 5), 10: (1.5, 5), 11: (0.5, 5),  # bottom
                               12: (0, 0.5), 13: (0, 1.5), 14: (0, 2.5), 15: (0, 3.5), 16: (0, 4.5)}

    # argument parser (used currently for graphics/no graphics, defaults to graphics)
    parser = argparse.ArgumentParser(description='drone simulator for pytello')
    feature_parser = parser.add_mutually_exclusive_group(required=False)
    feature_parser.add_argument('--graphics', dest='graphics', action='store_true')
    feature_parser.add_argument('--no-graphics', dest='graphics', action='store_false')
    parser.set_defaults(graphics=True)
    args = parser.parse_args()

    # create the simulator
    room = DroneSimulator(length=room_length, width=room_width, height=room_height, num_obstacles=num_obstacles,
                          num_moving_obstacles=num_moving_obstacles, num_asteroids=num_asteroids, is_simulated=True)
    drone = room.add_random_simulated_drone(id=1, team_color="red")
    drone.location.orientation = np.pi/2.0
    drone.location.x = 1.5
    drone.location.y = 2.5

    # create the GUI
    if (args.graphics):
        gui = DroneGUI(pixels_per_cm=200, room=room, marker_id_dict=marker_id_location_dict)
    else:
        gui = None

    # create the user thread to control the drone
    user_thread = threading.Thread(target=user_drone_code, args=(gui, drone, room, num_timesteps))
    user_thread.start()

    if (args.graphics):
        # run the main physics engine (checking each step to see if we are paused or unpaused)
        while (not gui.quit_pressed or room.get_timestep() < num_timesteps):
            if (gui.quit_pressed):
                print("Quitting!")
                break

            if (not gui.pause_pressed):
                room.advance_time()
                step = room.get_timestep()
            if (step % 100 == 0):
                print(room)

            gui.update_room(room)
            gui.update_extra_info(room.get_timestep())
            time.sleep(gui_pause)
    else:
        # run without graphics
        while (room.get_timestep() < num_timesteps):
            step = room.get_timestep()
            if (step % 1000 == 0):
                print("on step %d" % step)
            room.advance_time()
            # add a sleep or the user thread never gets run
            time.sleep(0.01)


