"""
GUI for AI class using drones.  Allows you to quickly create a map of
a room with obstacles for navigation and search.

Amy McGovern dramymcgovern@gmail.com
"""

from tkinter import *
import numpy as np
import math
from aiclass.droneSimulator import drone_radius

# Drone polygon coordinates (raw)
SHIP_SHAPE_UNSCALED = [(30, -50), (39, -40), (40, -35), (55, -60), (40, -60), (38, -68), (82, -68), (80, -60),
                       (70, -60), (40, -15), (40, 15), (70, 60), (80, 60), (82, 68), (38, 68), (40, 60), (55, 60),
                       (40, 35), (39, 40), (30, 50), (-30, 50), (-39, 40), (-40, 35), (-55, 60), (-40, 60), (-38, 68),
                       (-82, 68), (-80, 60), (-70, 60), (-40, 15), (-40, -15), (-70, -60), (-80, -60), (-82, -68),
                       (-38, -68), (-40, -60), (-55, -60), (-40, -35), (-39, -40), (-30, -50)]

SHIP_SHAPE_SCALED = np.multiply(drone_radius, SHIP_SHAPE_UNSCALED)

class DroneGUI:
    def __init__(self, pixels_per_cm, room):
        """
        Initialize a GUI with the specified scale

        :param pixels_per_cm: How many pixels are needed for one cm (used to scale the room)
        :param room: the droneRoom room (needed to draw and query obstacles)
        """
        self.root = Tk()
        self.room_frame = Frame(self.root, highlightthickness=5, highlightcolor="black", highlightbackground="black")
        self.room_frame.grid(row=0, column=0)
        self.extra_frame = Frame(self.root)
        self.extra_frame.grid(row=0, column=1)

        self.room_map = None
        self.obstacle_color = "#7575a3"
        self.goal_color = "green"
        self.start_color = "red"
        self.room = room
        self.asteroid_objects = dict()
        self.asteroid_labels = dict()
        self.drone_objects = dict()
        self.drone_labels = dict()
        self.quit_pressed = False
        self.pause_pressed = False

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
        self.room_canvas = Canvas(self.room_frame, width=canvas_width, height=canvas_height, bg="#ffffe6",
                                  highlightthickness=0, borderwidth=0)
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

        # Draw drones at their start location
        for drone in self.room.drones:
            translated_coordinates = self.get_translated_drone_polygon_coordinates(drone.location)
            print(translated_coordinates)
            id = self.room_canvas.create_polygon(translated_coordinates, fill=drone.team_color)
            self.drone_objects[drone.id] = id

            x = self.translate_location_to_pixel(drone.location.x)
            y = self.translate_location_to_pixel(drone.location.y)
            id = self.room_canvas.create_text(x, y, text=str(drone.id), fill="white")
            self.drone_labels[drone.id] = id

        # actually draw the room
        self.root.update()
        self.root.update_idletasks()


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

        for drone in self.room.drones:
            x = self.translate_location_to_pixel(drone.location.x)
            y = self.translate_location_to_pixel(drone.location.y)

            old_coords = self.room_canvas.coords(self.drone_objects[drone.id])
            dx = x - old_coords[0]
            dy = y - old_coords[1]

            self.room_canvas.move(self.drone_objects[drone.id], dx, dy)
            self.room_canvas.move(self.drone_labels[drone.id], dx, dy)

        # update the drawing
        self.root.update()
        self.root.update_idletasks()

    def _quit_button_pressed(self):
        """
        If quit is pressed, let the user know and be able to query it to stop nicely
        """
        self.quit_pressed = True

    def _pause_button_pressed(self):
        """
        Toggle the pause status
        """
        self.pause_pressed = not self.pause_pressed

    def draw_extra_info(self):
        """
        Draw a window with a quit button and some basic information
        """
        self.info_window = self.extra_frame
        #self.info_window.title("Drones Info")

        timestep = Label(self.info_window, text="Timestep: ")
        timestep.pack()

        self.timestep_label = Label(self.info_window, text="0")
        self.timestep_label.pack()

        self.quit_button = Button(self.info_window, text="Quit", command=self._quit_button_pressed)
        self.quit_button.pack()

        self.pause_button = Button(self.info_window, text="Pause", command=self._pause_button_pressed)
        self.pause_button.pack()

    def update_extra_info(self, timestep):
        """
        Update the extra info

        :param timestep:
        """
        self.timestep_label.config(text=str(timestep))
        self.info_window.update()
        self.root.update_idletasks()

    def get_translated_drone_polygon_coordinates(self, drone_position):
        """
        Translates coordinates from basic polygon to fit drone's current
        position and orientation.

        :param drone_position: Position of drone, should contain x, y, orientation
        :return: polygon coordinates, translated to match drone's position/orientation
        """
        x, y, angle = drone_position.x, drone_position.y, drone_position.orientation
        offset_x = self.translate_location_to_pixel(x)
        offset_y = self.translate_location_to_pixel(y)
        rotated_coordinates = [self.rotate(origin=(0, 0), point=shape_coord, angle=angle) for shape_coord in SHIP_SHAPE_SCALED]
        translated_coordinates = [(x+offset_x, y+offset_y) for x, y in rotated_coordinates]
        return translated_coordinates

    def rotate(self, origin, point, angle):
        """
        https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
        Rotate a point counterclockwise by a given angle around a given origin.

        :param angle: amount to rotate (radians)
        :param origin: point around which to rotate (always 0,0 since it is relative to ship's centroid)
        :param point: point that is being rotated (polygon coordinate)

        The angle should be given in radians.
        """
        ox, oy = origin
        px, py = point

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return qx, qy
