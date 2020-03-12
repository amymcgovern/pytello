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
# SHIP_SHAPE_UNSCALED = [(30, -50), (39, -40), (40, -35), (55, -60), (40, -60), (38, -68), (82, -68), (80, -60),
#                        (70, -60), (40, -15), (40, 15), (70, 60), (80, 60), (82, 68), (38, 68), (40, 60), (55, 60),
#                        (40, 35), (39, 40), (30, 50), (-30, 50), (-39, 40), (-40, 35), (-55, 60), (-40, 60), (-38, 68),
#                        (-82, 68), (-80, 60), (-70, 60), (-40, 15), (-40, -15), (-70, -60), (-80, -60), (-82, -68),
#                        (-38, -68), (-40, -60), (-55, -60), (-40, -35), (-39, -40), (-30, -50)]

SHIP_SHAPE_UNSCALED = [(-0.5,0.5), (0.5, 0), (-0.5, -0.5), (-0.5, 0.5)]
marker_id_location_dict = {1: (0.5, 0), 2: (1.5, 0), 3: (2.5, 0), # top
                           4: (3, 0.5), 5: (3, 1.5), 6: (3, 2.5), 7: (3, 3.5), 8: (3, 4.5), # right
                           9: (2.5, 5), 10: (1.5, 5), 11: (0.5, 5), # bottom
                           12: (0, 0.5), 13: (0, 1.5), 14: (0, 2.5), 15: (0, 3.5), 16: (0, 4.5)}

class DroneGUI:
    def __init__(self, pixels_per_cm, room):
        """
        Initialize a GUI with the specified scale

        :param pixels_per_cm: How many pixels are needed for one cm (used to scale the room)
        :param room: the droneRoom room (needed to draw and query obstacles)
        """
        self.root = Tk()
        self.root.title("PyTello Drone Simulator")
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
        self.points_labels = dict()
        self.score_labels = dict()
        self.damage_labels = dict()

        # scale_value is the number of cm that 1 pixel represents
        self.pixels_per_cm = pixels_per_cm
        self.SHIP_SHAPE_SCALED = np.multiply(drone_radius * 2.0 * self.pixels_per_cm, SHIP_SHAPE_UNSCALED)

        # draw the room and extra info
        self.draw_room()
        self.draw_extra_info()

    def translate_location_to_pixel(self, point):
        """
        translate a real-space coordinate to a pixel on the screen using the scales
        :param point: x or y location
        :return: the translated pixel location
        """
        return int(point * self.pixels_per_cm)

    def print_coords(self, event):
        print("clicked at", event.x, event.y)
        center_x = event.x
        center_y = event.y


    def draw_room(self):
        # each pixel is scale * 1 cm so multiply by 100 to get the width/height from the meters
        canvas_width = self.translate_location_to_pixel(self.room.length)
        canvas_height = self.translate_location_to_pixel(self.room.width)

        # draw the room
        self.room_canvas = Canvas(self.room_frame, width=canvas_width, height=canvas_height, bg="#ffffe6",
                                  highlightthickness=0, borderwidth=0)
        self.room_canvas.bind("<Button-1>", self.print_coords)
        self.room_canvas.pack()

        # how to draw a checkered canvas from
        # https://www.python-course.eu/tkinter_canvas.php
        # vertical lines every 10 m or ever meter if the room is < 10 wide or long
        if (self.room.length < 10 and self.room.width < 10):
            line_distance = self.translate_location_to_pixel(1)
        else:
            line_distance = self.translate_location_to_pixel(10)

        for x in range(line_distance, canvas_width, line_distance):
            # make the line red every 10 m
            if (x % (line_distance * 10) == 0):
                self.room_canvas.create_line(x, 0, x, canvas_height, fill="red", width=2)
            else:
                self.room_canvas.create_line(x, 0, x, canvas_height, fill="black")

        # horizontal lines at an interval of "line_distance" pixel
        for y in range(line_distance, canvas_height, line_distance):
            # make the line red every 10 m
            if (y % (line_distance * 10) == 0):
                self.room_canvas.create_line(0, y, canvas_width, y, fill="red", width=2)
            else:
                self.room_canvas.create_line(0, y, canvas_width, y, fill="black")

        # now loop through all the obstacles and draw them
        for asteroid in self.room.asteroids:
            #print(asteroid.location.x, asteroid.location.y, asteroid.id)
            x = self.translate_location_to_pixel(asteroid.location.x)
            y = self.translate_location_to_pixel(asteroid.location.y)
            radius = self.translate_location_to_pixel(asteroid.radius)

            id = self.room_canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=asteroid.fill_color)
            self.asteroid_objects[asteroid.id] = id

            id = self.room_canvas.create_text(x, y, text=str(asteroid.id), fill="white")
            self.asteroid_labels[asteroid.id] = id

        # Draw drones at their start location
        for drone in self.room.drones:
            translated_coordinates = self.get_translated_drone_polygon_coordinates(drone.location)
            #print(translated_coordinates)
            id = self.room_canvas.create_polygon(translated_coordinates, fill=drone.team_color)
            radius = self.translate_location_to_pixel(drone_radius)

            x = self.translate_location_to_pixel(drone.location.x)
            y = self.translate_location_to_pixel(drone.location.y)
            # id = self.room_canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=drone.team_color)
            self.drone_objects[drone.id] = id

            id = self.room_canvas.create_text(x, y, text=str(drone.location.z), fill="black")
            self.drone_labels[drone.id] = id

        # draw the marker ids
        for marker_id in marker_id_location_dict.keys():
            (x, y) = marker_id_location_dict[marker_id]
            if (y == 0):
                y = 0.05
            if (x == self.room.length):
                x -= 0.05
            if (x == 0):
                x = 0.05
            if (y == self.room.width):
                y -= 0.05

            x = self.translate_location_to_pixel(x)
            y = self.translate_location_to_pixel(y)
            id = self.room_canvas.create_text(x, y, text=str(marker_id), fill="red")


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

            old_coords = self.room_canvas.coords(self.drone_labels[drone.id])
            dx = x - old_coords[0]
            dy = y - old_coords[1]

            self.room_canvas.move(self.drone_objects[drone.id], dx, dy)
            self.room_canvas.move(self.drone_labels[drone.id], dx, dy)
            height_str = str("%0.02f" % drone.location.z)
            self.room_canvas.itemconfigure(self.drone_labels[drone.id], text=height_str)

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

        # create a frame with the time steps
        time_step_frame = Frame(self.extra_frame)
        time_step_frame.grid(row=0, column=0, pady=10, padx=10)

        timestep = Label(time_step_frame, text="Timestep: ")
        timestep.grid(row=0, column=0)

        self.timestep_label = Label(time_step_frame, text="000000")
        self.timestep_label.grid(row=0, column=1)

        # current scores for each drone
        score_frame = Frame(self.extra_frame)
        score_frame.grid(row=1, column=0, pady=10)
        label = Label(score_frame, text="Drone info")
        label.grid(row=0, columnspan=3)

        id_label = Label(score_frame, text="Id")
        id_label.grid(row=1, column=0)

        score_label = Label(score_frame, text="Score")
        score_label.grid(row=1, column=1)

        damage_label = Label(score_frame, text="Damage")
        damage_label.grid(row=1, column=2)

        # draw the asteroids and their resources
        row_id = 2
        for drone in self.room.drones:
            id_label = Label(score_frame, text=str("{:d}".format(drone.id)))
            id_label.grid(row=row_id, column=0)

            self.score_labels[drone.id] = Label(score_frame, text=str("{:.2f}".format(drone.score)))
            self.score_labels[drone.id].grid(row=row_id, column=1)

            self.damage_labels[drone.id] = Label(score_frame, text=str("{:.2f}".format(drone.damage)))
            self.damage_labels[drone.id].grid(row=row_id, column=2)

            row_id += 1

        # line up the asteroid info next
        asteroid_frame = Frame(self.extra_frame)
        asteroid_frame.grid(row=2, column=0, pady=10)
        label = Label(asteroid_frame, text="Asteroid info")
        label.grid(row=0, columnspan=2)

        id_label = Label(asteroid_frame, text="Id")
        id_label.grid(row=1, column=0)

        score_label = Label(asteroid_frame, text="Points")
        score_label.grid(row=1, column=1)

        # draw the asteroids and their resources
        row_id = 2
        for asteroid in self.room.asteroids:
            if(asteroid.is_mineable):
                id_label = Label(asteroid_frame, text=str("{:d}".format(asteroid.id)))
                id_label.grid(row=row_id, column=0)

                self.points_labels[asteroid.id] = Label(asteroid_frame, bg=asteroid.fill_color, fg="white",
                                                        text=str("{:.2f}".format(asteroid.resources)))
                self.points_labels[asteroid.id].grid(row=row_id, column=1)

                row_id += 1

        # row of buttons on the bottom
        quit_frame = Frame(self.extra_frame)
        quit_frame.grid(row=3, column=0, pady=20)

        self.pause_button = Button(quit_frame, text="Pause", command=self._pause_button_pressed)
        self.pause_button.grid(row=0, column=0, padx=10)

        self.quit_button = Button(quit_frame, text="Quit", command=self._quit_button_pressed)
        self.quit_button.grid(row=0, column=1, padx=10)


    def update_extra_info(self, timestep):
        """
        Update the extra info

        :param timestep:
        """

        # update the stuff that changes
        self.timestep_label.config(text="%06d" % timestep)

        for drone in self.room.drones:
            self.damage_labels[drone.id].config(text=str("{:.2f}".format(drone.damage)))
            self.score_labels[drone.id].config(text=str("{:.2f}".format(drone.score)))

        self.extra_frame.update()
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
        rotated_coordinates = [self.rotate(origin=(0, 0), point=shape_coord, angle=angle) for shape_coord in self.SHIP_SHAPE_SCALED]
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
