"""
GUI for AI class using drones.  Allows you to quickly create a map of
a room with obstacles for navigation and search.

Amy McGovern dramymcgovern@gmail.com
"""

from tkinter import *
import numpy as np

class DroneGUI:
    def __init__(self, pixels_per_cm, room):
        """
        Initialize a GUI with the specified scale

        :param pixels_per_cm: How many pixels are needed for one cm (used to scale the room)
        :param room: the droneRoom room (needed to draw and query obstacles)
        """
        self.root = Tk()
        self.room_map = None
        self.obstacle_color = "#7575a3"
        self.goal_color = "green"
        self.start_color = "red"
        self.room = room
        self.asteroid_objects = dict()
        self.asteroid_labels = dict()

        # scale_value is the number of cm that 1 pixel represents
        self.pixels_per_cm = pixels_per_cm

    def translate_location_to_pixel(self, point):
        """
        translate a real-space coordinate to a pixel on the screen using the scales
        :param point: x or y location
        :return: the translated pixel location
        """
        return int(point * self.pixels_per_cm)

    def draw_room(self):
        # each pixel is scale * 1 cm so multiply by 100 to get the width/height from the meters
        canvas_width = self.translate_location_to_pixel(self.room.length)
        canvas_height = self.translate_location_to_pixel(self.room.width)

        # draw the room
        self.room_canvas = Canvas(self.root, width=canvas_width, height=canvas_height, bg="#ffffe6")
        self.room_canvas.pack()

        # how to draw a checkered canvas from
        # https://www.python-course.eu/tkinter_canvas.php
        # vertical lines every 10 m
        line_distance = self.translate_location_to_pixel(10)
        for x in range(line_distance, canvas_width, line_distance):
            if (x % (line_distance * 10) == 0):
                self.room_canvas.create_line(x, 0, x, canvas_height, fill="red", width=2)
            else:
                self.room_canvas.create_line(x, 0, x, canvas_height, fill="black")

        # horizontal lines at an interval of "line_distance" pixel
        for y in range(line_distance, canvas_height, line_distance):
            if (y % (line_distance * 10) == 0):
                self.room_canvas.create_line(0, y, canvas_width, y, fill="red", width=2)
            else:
                self.room_canvas.create_line(0, y, canvas_width, y, fill="black")

        # now loop through all the obstacles and draw them
        for asteroid in self.room.asteroids:
            x = self.translate_location_to_pixel(asteroid.location.x)
            y = self.translate_location_to_pixel(asteroid.location.y)
            radius = self.translate_location_to_pixel(asteroid.radius)

            if (asteroid.is_mineable):
                # https://stackoverflow.com/questions/41383849/setting-the-fill-of-a-rectangle-drawn-with-canvas-to-an-rgb-value
                fill_color = "#%02x%02x%02x" % (0, int(asteroid.resources * 256), int(asteroid.resources * 256))
            else:
                fill_color = "#B59892"

            id = self.room_canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=fill_color)
            self.asteroid_objects[asteroid.id] = id

            id = self.room_canvas.create_text(x, y, text=str(asteroid.id), fill="white")
            self.asteroid_labels[asteroid.id] = id


        # actually draw the room
        self.root.update()

    def update_room(self, room):
        """
        Update the objects inside the room (but no need to redraw the canvas)
        :param room: the room simulator object (so we can redraw locations)
        :return:
        """
        for asteroid in self.room.asteroids:
            x = self.translate_location_to_pixel(asteroid.location.x)
            y = self.translate_location_to_pixel(asteroid.location.y)
            radius = self.translate_location_to_pixel(asteroid.radius)

            old_coords = self.room_canvas.coords(self.asteroid_labels[asteroid.id])
            dx = x - old_coords[0]
            dy = y - old_coords[1]

            self.room_canvas.move(self.asteroid_labels[asteroid.id], dx, dy)
            self.room_canvas.move(self.asteroid_objects[asteroid.id], dx, dy)


        # update the drawing
        self.root.update()
