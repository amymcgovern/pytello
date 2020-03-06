"""
A drone simulator for the AI class

author: Amy McGovern <dramymcgovern@gmail.com>
"""

from aiclass.droneSimulator import DroneSimulator, Drone, Velocity
from aiclass.droneGUI import DroneGUI
import time

if __name__ == "__main__":
    room_length = 30
    room_width = 40
    room_height=3
    num_mission_pads = 8
    num_obstacles = 3
    num_timesteps = 1000
    gui_pause = 0.02
    num_asteroids = num_mission_pads - num_obstacles

    room = DroneSimulator(length=room_length, width=room_width, height=room_height, num_obstacles=num_obstacles, num_asteroids=num_asteroids, is_simulated=True)
    drone = room.add_random_simulated_drone(id=1, team_color="red")
    drone.set_velocity(Velocity(x=1.3, y=1, z=0.1, rotational=0))

    gui = DroneGUI(pixels_per_cm=20, room=room)
    gui.draw_room()
    gui.draw_extra_info()

    # now advance time
    step = 0
    while (not gui.quit_pressed or step < num_timesteps):
        if (gui.quit_pressed):
            print("Quitting!")
            break

        if (not gui.pause_pressed):
            room.advance_time()
            step += 1

        gui.update_room(room)
        gui.update_extra_info(step)
        time.sleep(gui_pause)


