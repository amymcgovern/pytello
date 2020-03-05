"""
A drone simulator for the AI class

author: Amy McGovern <dramymcgovern@gmail.com>
"""

from aiclass.droneRoom import DroneRoom
from aiclass.droneGUI import DroneGUI
import time

if __name__ == "__main__":
    room_length = 30
    room_width = 40
    num_mission_pads = 8
    num_obstacles = 3
    num_timesteps = 1000
    gui_pause = 0.02
    num_asteroids = num_mission_pads - num_obstacles

    room = DroneRoom(length=room_length, width=room_width, num_obstacles=num_obstacles, num_asteroids=num_asteroids, is_simulated=True)

    gui = DroneGUI(pixels_per_cm=20, room=room)
    gui.draw_room()

    # now advance time
    for step in range(1, num_timesteps):
        room.advance_time()
        gui.update_room(room)
        time.sleep(gui_pause)

    input("press return to quit")

