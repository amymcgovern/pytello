"""
A drone simulator for the AI class

author: Amy McGovern <dramymcgovern@gmail.com>
"""

from aiclass.droneRoom import DroneRoom
from aiclass.droneGUI import DroneGUI

if __name__ == "__main__":
    room_length = 30
    room_width = 40
    num_mission_pads = 8
    num_obstacles = 3
    num_asteroids = num_mission_pads - num_obstacles

    room = DroneRoom(length=room_length, width=room_width, num_obstacles=num_obstacles, num_asteroids=num_asteroids, is_simulated=True)

    gui = DroneGUI(pixels_per_cm=20, room=room)
    gui.draw_room()
    input("press return to quit")

