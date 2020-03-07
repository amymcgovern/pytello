"""
A drone simulator for the AI class

author: Amy McGovern <dramymcgovern@gmail.com>
"""

from aiclass.droneSimulator import DroneSimulator, Drone, Velocity
from aiclass.droneGUI import DroneGUI
import time
import threading

def user_drone_code(gui, drone, droneSimulator):
    """
    This is where you put any of your user control code

    :param gui: link to the GUI so you know when the quit or pause button are pressed
    :param drone: the drone being controlled
    :param droneSimulator: the simulator for the drone
    :return:
    """

    # run until the quit button is pressed
    while (not gui.quit_pressed):
        step = droneSimulator.get_timestep()
        if (step == 1):
            print("Takeoff")
            drone.takeoff()
            print("Done with takeoff")
        elif (step == 200):
            print("Landing")
            drone.land()
            print("Done with landing")
        step += 1

        # make sure you yield even for a fraction of a second in the user thread so that
        # the main simulator can run!
        time.sleep(0.01)

if __name__ == "__main__":
    room_length = 30
    room_width = 40
    room_height=3
    num_mission_pads = 8
    num_obstacles = 3
    num_timesteps = 10000
    gui_pause = 0.05
    num_asteroids = num_mission_pads - num_obstacles

    # create the simulator
    room = DroneSimulator(length=room_length, width=room_width, height=room_height, num_obstacles=num_obstacles, num_asteroids=num_asteroids, is_simulated=True)
    drone = room.add_random_simulated_drone(id=1, team_color="red")

    # create the GUI
    gui = DroneGUI(pixels_per_cm=20, room=room)

    # create the user thread to control the drone
    user_thread = threading.Thread(target=user_drone_code, args=(gui, drone, room))
    user_thread.start()

    # run the main physics engine (checking each step to see if we are paused or unpaused)
    while (not gui.quit_pressed or room.get_timestep() < num_timesteps):
        if (gui.quit_pressed):
            print("Quitting!")
            break

        if (not gui.pause_pressed):
            room.advance_time()

        gui.update_room(room)
        gui.update_extra_info(room.get_timestep())
        time.sleep(gui_pause)

