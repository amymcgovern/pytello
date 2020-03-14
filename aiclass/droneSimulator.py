"""
Manages the room and obstacles where the drone flies in (represents
a real room but can be used without an actual room if the drone is in simulated mode).
This is a very specific implementation that mimics the spacesettlers code used by
the rest of the AI class.
www.github.com/amymcgovern/spacesettlers
"""

import numpy as np
import time
from datetime import datetime
from pytello.Tello import ensure_distance_within_limits, ensure_speed_within_limits
import copy

# some user defined parameters
max_asteroid_speed = 0.3  # m/s
asteroid_radius = 0.1  # in meters (this is large initially)
drone_radius = 0.05  # in meters
score_timesteps = 100  # number of time ticks between scores on the same pad
crash_timesteps = 30 # number of time tickets between crashes on the same pad
asteroid_damage = 5 # constant damage score for hitting a non-mineable asteroid
move_noise = 0.1 # noise variance in x, y, z in m/s
turn_noise = 0.02 # noise variance in radians

class Position:
    def __init__(self, x, y, z=0, orientation=0):
        """
        Create a new position with orientation optional

        :param x: x
        :param y: y
        :param z: z (height, optional)
        :param orientation: optional orientation (needed for movement)
        """
        self.x = x
        self.y = y
        self.z = z
        self.orientation = orientation

    def distance_from_position(self, other):
        """
        Compute the euclidean distance to the other position
        :param other:
        :return: euclidean distance
        """
        dist = np.sqrt(np.square(self.x - other.x) + np.square(self.y - other.y) + np.square(self.z - other.z))
        return dist

    def distance_from_x_y(self, x, y):
        """
        Compute the euclidean distance to the other position
        :param other:
        :return: euclidean distance
        """
        dist = np.sqrt(np.square(self.x - x) + np.square(self.y - y))
        return dist


class Velocity:
    """
    Velocity vector (by components)
    """

    def __init__(self, x, y, z, rotational):
        self.x = x
        self.y = y
        self.z = z
        self.rotational = rotational


class Asteroid:
    def __init__(self, position, is_mineable, id, is_moveable):
        """
        Create an asteroid

        :param position: starting position
        :param is_mineable: is it mineable?  If so, create the resources
        :param id: id (mission pad!)
        :param is_moveable: can the asteroid move on its own (in the simulator) True if so.
        """
        self.location = position
        self.is_mineable = is_mineable
        self.radius = asteroid_radius
        self.id = id
        self.is_moveable = is_moveable
        self.resources = 0
        self.damage = 0

        self.reset_and_move()


    def reset_and_move(self):
        """
        Reset the asteroid's resources and move it to a new location
        :return:
        """
        if (self.is_mineable):
            self.resources = np.random.random()
            self.damage = 0
        else:
            # you can't get any resources from non-mineable asteroids
            # but you do get damage
            self.resources = 0
            self.damage = asteroid_damage

        if (self.is_moveable):
            x = np.random.random() * 2.0 * max_asteroid_speed - max_asteroid_speed
            y = np.random.random() * 2.0 * max_asteroid_speed - max_asteroid_speed
            rotational_change = (np.random.random() * 0.2) - 0.1
            self.velocity = Velocity(x, y, z=0, rotational=rotational_change)
        else:
            self.velocity = Velocity(0, 0, 0, 0)

        # reset the color to match new resources
        if (self.is_mineable):
            # https://stackoverflow.com/questions/41383849/setting-the-fill-of-a-rectangle-drawn-with-canvas-to-an-rgb-value
            self.fill_color = "#%02x%02x%02x" % (0, int(self.resources * 256), int(self.resources * 256))
        else:
            self.fill_color = "#B59892"


class Drone:
    def __init__(self, position, id, team_color, tello):
        """
        Create a drone object for the simulator (and use the real drone if this isn't simulation)

        :param position: starting Position of the drone
        :param id: UUID used to identify this drone
        :param team_color: color to paint the drone (set by the user)
        :param tello: pyTello instance - set to None for simulated drones
        """
        self.location = position
        self.velocity = Velocity(x=0, y=0, z=0, rotational=0)
        self.id = id
        self.radius = drone_radius
        self.team_color = team_color
        self._tello = tello
        self.is_crashed = False
        self.constant_speed = 0.5  # used because the tello allows a speed to be set, defaulting to 0.5 m/s
        self.last_score_timestep = dict()  # used to track time steps when you score on a pad
        self.last_crash_timestep = dict() # used to track when you crashed into an obstacle
        self.score = 0
        self.damage = 0

    def set_location(self, position):
        """
        Set the drone to a specific (x, y, z) location

        :param position: Position object
        """
        self.location = position

    def _set_velocity(self, velocity):
        """
        Set the drone to a specific velocity.  Debugging only.  Otherwise it should be set
        through movement calls
        :param velocity: Velocity object
        """
        self.velocity = velocity

    def takeoff(self, seconds_to_wait=3):
        """
        Send takeoff to the drone (if it is exists) and otherwise set the simulator to move up in z

        :param seconds_to_wait: optional number of seconds to sleep waiting for the takeoff to finish (default 3)
        :return: True if the command was sent and False otherwise
        """
        if (self._tello is not None):
            return self._tello.takeoff(seconds_to_wait=seconds_to_wait)
        else:
            self.velocity.z = 0.2
            time.sleep(seconds_to_wait)
            self.velocity.z = 0.0

    def land(self, seconds_to_wait=3):
        """
        Send takeoff to the drone (if it is exists) and otherwise set the simulator to move up in z

        :param seconds_to_wait: optional number of seconds to sleep waiting for the land to finish (default 3)
        :return: True if the command was sent and False otherwise
        """
        if (self._tello is not None):
            return self._tello.land(seconds_to_wait=seconds_to_wait)
        else:
            self.velocity.z = -0.2

            start_time = datetime.now()
            new_time = datetime.now()
            diff = (new_time - start_time).seconds + ((new_time - start_time).microseconds / 1000000.0)

            while (diff < seconds_to_wait):
                time.sleep(0.01)
                new_time = datetime.now()
                diff = (new_time - start_time).seconds + ((new_time - start_time).microseconds / 1000000.0)
                if (self.location.z < 0.05):
                    self.velocity.z = 0.0
                    self.location.z = 0.0

            self.velocity.z = 0.0

    def sleep(self, timeout):
        """
        Sleeps the requested number of seconds

        :param timeout: number of seconds to sleep
        :return:
        """
        if (self._tello is None):
            time.sleep(timeout)
        else:
            self._tello.sleep(timeout)

    def hover(self, timeToHover=None):
        """
        Makes the drone hover - optionally stay in hover for the time specified (which means all velocity is stopped)
        :param timeToHover: time to sleep (optional)
        :return: if it hovers or not
        """
        if (self._tello is not None):
            return self._tello.hover(timeToHover)
        else:
            # stop all motion
            self.velocity.x = 0
            self.velocity.y = 0
            self.velocity.z = 0
            self.velocity.rotational = 0

            if (timeToHover is not None):
                time.sleep(timeToHover)

    def forward_cm(self, cm, speed=None):
        """
        Moves ONLY FORWARD in cm.  If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move FORWARDS in cm [20,500]
        :param speed: optional command to tell it to fly forward that much at a speed in the range [10,100] cm/s
        """

        if (self._tello is None):
            if (self.location.z > 0):
                distance = ensure_distance_within_limits(cm)

                if (speed is None):
                    speed = self.constant_speed
                speed = ensure_speed_within_limits(speed)
                if(speed < 10):
                    # Prevent velocity from being set to 0 ie infinite loop
                    return

                # set the right velocities
                self.velocity.x = np.cos(self.location.orientation) * speed
                self.velocity.y = np.sin(self.location.orientation) * speed
                self.velocity.z = 0
                self.velocity.rotational = 0

                # and now check the distance traveled and stop if you reach it or if you crash
                orig_location = copy.copy(self.location)
                target_distance_m = distance / 100.0

                while (orig_location.distance_from_x_y(self.location.x,
                                                       self.location.y) < target_distance_m and not self.is_crashed):

                    time.sleep(0.02)

                # stop when you reach the right location
                self.velocity.x = 0
                self.velocity.y = 0

        else:
            # tell the tello to move
            self._tello.forward_cm(cm, speed)

    def backward_cm(self, cm, speed=None):
        """
        Moves ONLY BACKWARDS in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move BACKWARDS in cm [20,500]
        :param speed: optional command to tell it to fly backward that much at a speed in the range [10,100] cm/s
        """

        if (self._tello is None):
            if (self.location.z > 0):
                distance = ensure_distance_within_limits(cm)

                if (speed is None):
                    speed = self.constant_speed
                speed = ensure_speed_within_limits(speed)
                if(speed < 10):
                    # Prevent velocity from being set to 0 ie infinite loop
                    return

                # set the right velocities
                self.velocity.x = -np.cos(self.location.orientation) * speed
                self.velocity.y = -np.sin(self.location.orientation) * speed
                self.velocity.z = 0
                self.velocity.rotational = 0

                # and now check the distance traveled and stop if you reach it or if you crash
                orig_location = copy.copy(self.location)
                target_distance_m = distance / 100.0

                while (orig_location.distance_from_x_y(self.location.x,
                                                       self.location.y) < target_distance_m and not self.is_crashed):
                    time.sleep(0.02)

                # stop when you reach the right location
                self.velocity.x = 0
                self.velocity.y = 0

        else:
            # tell the tello to move
            self._tello.backward_cm(cm, speed)

    def left_cm(self, cm, speed=None):
        """
        Moves ONLY LEFT in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move LEFT in cm [20,500]
        :param speed: optional command to tell it to fly left that much at a speed in the range [10,100] cm/s
        """

        if (self._tello is None):
            if (self.location.z > 0):
                distance = ensure_distance_within_limits(cm)
                
                if (speed is None):
                    speed = self.constant_speed
                speed = ensure_speed_within_limits(speed)
                if(speed < 10):
                    # Prevent velocity from being set to 0 ie infinite loop
                    return

                # set the right velocities
                self.velocity.x = -np.sin(self.location.orientation) * speed
                self.velocity.y = -np.cos(self.location.orientation) * speed
                self.velocity.z = 0
                self.velocity.rotational = 0

                # and now check the distance traveled and stop if you reach it or if you crash
                orig_location = copy.copy(self.location)
                target_distance_m = distance / 100.0

                while (orig_location.distance_from_x_y(self.location.x,
                                                       self.location.y) < target_distance_m and not self.is_crashed):
                    time.sleep(0.02)

                # stop when you reach the right location
                self.velocity.x = 0
                self.velocity.y = 0

        else:
            # tell the tello to move
            self._tello.left_cm(cm, speed)

    def right_cm(self, cm, speed=None):
        """
        Moves ONLY RIGHT in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move RIGHT in cm [20,500]
        :param speed: optional command to tell it to fly right that much at a speed in the range [10,100] cm/s
        """

        if (self._tello is None):
            if (self.location.z > 0):
                distance = ensure_distance_within_limits(cm)

                if (speed is None):
                    speed = self.constant_speed
                speed = ensure_speed_within_limits(speed)
                if(speed < 10):
                    # Prevent velocity from being set to 0 ie infinite loop
                    return

                # set the right velocities
                self.velocity.x = np.sin(self.location.orientation) * speed
                self.velocity.y = np.cos(self.location.orientation) * speed
                print(self.velocity.x, self.velocity.y)
                self.velocity.z = 0
                self.velocity.rotational = 0

                # and now check the distance traveled and stop if you reach it or if you crash
                orig_location = copy.copy(self.location)
                target_distance_m = distance / 100.0

                while (orig_location.distance_from_x_y(self.location.x,
                                                       self.location.y) < target_distance_m and not self.is_crashed):
                    time.sleep(0.01)

                # stop when you reach the right location
                self.velocity.x = 0
                self.velocity.y = 0

        else:
            # tell the tello to move
            self._tello.right_cm(cm, speed)

    def up_cm(self, cm, speed=None):
        """
        Moves ONLY UP in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move UP in cm [20,500]
        :param speed: optional command to tell it to fly up that much at a speed in the range [10,100] cm/s
        """

        if (self._tello is None):
            if (self.location.z > 0):
                distance = ensure_distance_within_limits(cm)

                if (speed is None):
                    speed = self.constant_speed
                speed = ensure_speed_within_limits(speed)
                if(speed < 10):
                    # Prevent velocity from being set to 0 ie infinite loop
                    return

                # set the right velocities
                self.velocity.x = 0
                self.velocity.y = 0
                self.velocity.z = speed
                self.velocity.rotational = 0

                # and now check the distance traveled and stop if you reach it or if you crash
                orig_location = copy.copy(self.location)
                target_distance_m = distance / 100.0

                while (orig_location.distance_from_position(self.location) < target_distance_m and not self.is_crashed):
                    time.sleep(0.01)

                # stop when you reach the right location
                self.velocity.x = 0
                self.velocity.y = 0
                self.velocity.z = 0
        else:
            # tell the tello to move
            self._tello.up_cm(cm, speed)

    def down_cm(self, cm, speed=None):
        """
        Moves ONLY DOWN in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move RIGHT in cm [20,500]
        :param speed: optional command to tell it to fly down that much at a speed in the range [10,100] cm/s
        """

        if (self._tello is None):
            if (self.location.z > 0):
                distance = ensure_distance_within_limits(cm)
                
                if (speed is None):
                    speed = self.constant_speed
                speed = ensure_speed_within_limits(speed)
                if(speed < 10):
                    # Prevent velocity from being set to 0 ie infinite loop
                    return

                # set the right velocities
                self.velocity.x = 0
                self.velocity.y = 0
                self.velocity.z = -speed
                self.velocity.rotational = 0

                # and now check the distance traveled and stop if you reach it or if you crash
                orig_location = copy.copy(self.location)
                target_distance_m = distance / 100.0

                while (orig_location.distance_from_position(self.location) < target_distance_m and not self.is_crashed):
                    time.sleep(0.01)

                # stop when you reach the right location
                self.velocity.x = 0
                self.velocity.y = 0
                self.velocity.z = 0
        else:
            # tell the tello to move
            self._tello.down_cm(cm, speed)

    def set_speed(self, new_speed):
        """
        Set the default speed to the value specified in the range [10,100]
        :param new_speed:
        :return: True if the command suceeded and False otherwise
        """

        # keep track of the new speed in the simulator
        speed = ensure_speed_within_limits(new_speed)
        self.constant_speed = speed

        # and send it to the tello if it exists
        if (self._tello is not None):
            # tell the tello to move
            self._tello.set_speed(new_speed)


class DroneSimulator:
    def __init__(self, length, width, height, num_obstacles, num_moving_obstacles, num_asteroids, is_simulated):
        """
        Create the empty droneRoom for flying. The user needs to add the drones (since there may be more than one
        and even more than one team)

        :param length: length of the room
        :param width: width of the room
        :param height: height of the room (if the drone exceeds this, it is "crashed" on the ground where it exceeded it
        :param num_obstacles: number of obstacles (things to not land on)
        :param num_moving_obstacles: number of obstacles that move (in the real world and in simulation)
        :param num_asteroids: number of asteroids (things that give you resources)
        :param is_simulated: is this a simulator or flying in the real-world?
        """
        self.length = length
        self.width = width
        self.height = height
        self.num_obstacles = num_obstacles
        self.num_asteroids = num_asteroids
        self.is_simulated = is_simulated
        self.asteroids = list()
        self.physics_timestep = 0.05
        self.noise_timestep = 0
        self.sim_timestep = 0
        self.drones = list()

        if (self.is_simulated):
            # if we are in simulation mode, automatically create the asteroid and obstacle locations
            self.__initialize_asteroids(num_obstacles, num_moving_obstacles, num_asteroids)
        else:
            print(
                "Real world mode: make sure you initialize the locations and velocities for the asteroids and obstacles and drone")

    def add_drone(self, drone):
        """
        Add the drone (simulated if we are in simulation mode and real if not) to the list of drones

        :param drone: drone object (either pyTello or a simulated pyTello)
        """
        self.drones.append(drone)

    def add_asteroid(self, position, id, is_mineable, is_moveable):
        """
        add the asteroid at the specified location to the list

        :param position: Position for the new asteroid/obstacle
        :param is_mineable: True if it is a mineable asteroid and False if it is an obstacle
        :return: nothing
        """
        asteroid = Asteroid(position, is_mineable, id, is_moveable)
        self.asteroids.append(asteroid)

    def __initialize_asteroids(self, num_obstacles, num_moving_obstacles, num_asteroids):
        """
        Create the specified number of asteroids and ensure they are in free space
        :param num_obstacles: number of obstacles e.g. non-mineable asteroids
        :param num_moving_obstacles: number of moving real-world/simulated obstacles
        :param num_asteroids: number of mineable asteroids
        :return:
        """

        id = 1
        for i in range(0, num_moving_obstacles):
            position = self.get_random_free_location(free_radius=3.0*asteroid_radius)
            self.add_asteroid(position, is_mineable=False, id=id, is_moveable=True)
            id += 1

        for i in range(num_moving_obstacles, num_obstacles):
            position = self.get_random_free_location(free_radius=3.0*asteroid_radius)
            self.add_asteroid(position, is_mineable=False, id=id, is_moveable=False)
            id += 1

        for i in range(0, num_asteroids):
            position = self.get_random_free_location(free_radius=3.0*asteroid_radius)
            self.add_asteroid(position, is_mineable=True, id=id, is_moveable=False)
            id += 1

    def add_random_simulated_drone(self, id, team_color):
        """
        Creates a new drone in a random location

        :return the random drone
        """
        position = self.get_random_free_location(free_radius=drone_radius * 3.0)
        position.orientation = np.random.random() * np.pi * 2.0
        drone = Drone(position, id, tello=None, team_color=team_color)
        self.add_drone(drone)
        return drone

    def get_random_free_location(self, free_radius):
        """
        Return a random location that does not overlap any asteroids within the specified radius.
        Note locations all start on the ground (z = 0 and at orientation=0)

        :param free_radius:
        :return:
        """
        num_try = 0
        max_tries = 30
        x = 0
        y = 0

        while (num_try < max_tries):
            # try a location
            x = np.random.random() * self.length
            y = np.random.random() * self.width

            if ((x - free_radius) < 0 or (y - free_radius) < 0 or
                (x + free_radius) > self.length or (y + free_radius) > self.width):
                # it is too close to a wall, don't bother to check other asteroids
                loc_found = False
            else:
                loc_found = True

            # make sure it is far enough away
            for asteroid in self.asteroids:
                dist = asteroid.location.distance_from_x_y(x, y)
                if (dist < free_radius):
                    loc_found = False
                    break

            # if we found a good location, quit the loop
            if (loc_found):
                break

            num_try += 1

        if (num_try == max_tries):
            print("Giving up on initializing, taking a bad one potentially")

        return Position(x, y, z=0, orientation=0)

    def get_timestep(self):
        """
        Get the current simulator timestep
        :return:
        """
        return int(self.sim_timestep)

    def advance_time(self):
        """
        Advance time for the simulator one step

        :return:
        """

        # step one, move all the asteroids
        for asteroid in self.asteroids:
            # print(asteroid.location.x, asteroid.location.y)
            new_x = asteroid.location.x + asteroid.velocity.x * self.physics_timestep
            new_y = asteroid.location.y + asteroid.velocity.y * self.physics_timestep
            new_angle = asteroid.location.orientation + (asteroid.velocity.rotational * self.physics_timestep)
            new_angle = np.mod(new_angle, np.pi * 2.0)

            # handle wall collisions (note, collisions between asteroids are ignored since
            # we assume they will not happen in the real-world
            if (new_x - asteroid_radius < 0 or new_x + asteroid_radius > self.length):
                new_x = asteroid.location.x
                asteroid.velocity.x = -asteroid.velocity.x

            if (new_y - asteroid_radius < 0 or new_y + asteroid_radius > self.width):
                new_y = asteroid.location.y
                asteroid.velocity.y = -asteroid.velocity.y

            # update the location
            asteroid.location.x = new_x
            asteroid.location.y = new_y
            asteroid.location.orientation = new_angle

        # update the drone's location
        for drone in self.drones:
            if (drone.is_crashed):
                # only move drones that are not crashed
                continue

            # add a small amount of gaussian noise to the velocities
            if (self.noise_timestep % 10 == 0):
                self.x_noise = np.random.normal() * move_noise * drone.velocity.x
                self.y_noise = np.random.normal() * move_noise * drone.velocity.y
            x_noise = self.x_noise
            y_noise = self.y_noise
            self.noise_timestep += 1
            #print(x_noise, y_noise)

            new_x = drone.location.x + (drone.velocity.x + x_noise) * self.physics_timestep
            new_y = drone.location.y + (drone.velocity.y + y_noise) * self.physics_timestep
            new_z = drone.location.z + drone.velocity.z * self.physics_timestep
            new_angle = drone.location.orientation + (drone.velocity.rotational + (np.random.normal() * turn_noise)) * self.physics_timestep
            new_angle = np.mod(new_angle, np.pi * 2.0)

            # wall or ceiling collisions cause a crash
            if (new_x - drone_radius < 0 or new_x + drone_radius > self.length or
                    new_y - drone_radius < 0 or new_y + drone_radius > self.width or
                    new_z < 0 or new_z + drone_radius > self.height):
                print("Drone crashed! %f %f %f" % (new_x, new_y, new_z))
                new_z = 0
                drone.is_crashed = True
                drone.velocity = Velocity(0, 0, 0, 0)

            # update the location
            # print(new_x, new_y, new_z)
            drone.location.x = new_x
            drone.location.y = new_y
            drone.location.z = new_z
            drone.location.orientation = new_angle

        # check to see if a drone landed on a pad or crashed into a non-mineable asteroid
        for drone in self.drones:
            # has the drone landed and not crashed
            if (drone.location.z == 0 and not drone.is_crashed):
                # check all the mineable asteroids and see if we have landed on one
                for asteroid in self.asteroids:
                    if (asteroid.is_mineable):
                        # it is mineable.  see how far away we are in 3D
                        dist = drone.location.distance_from_position(asteroid.location)

                        # if we are landed on it, ensure that we didn't land on it recently
                        if (dist <= asteroid_radius):
                            if ((asteroid.id not in drone.last_score_timestep) or
                                    (self.sim_timestep - drone.last_score_timestep[asteroid.id] >= score_timesteps)):
                                drone.score += asteroid.resources
                                drone.last_score_timestep[asteroid.id] = self.sim_timestep
                                asteroid.reset_and_move()
            else:
                for asteroid in self.asteroids:
                    if (not asteroid.is_mineable):
                        # non-mineable, ensure we didn't crash inside the vertical projection
                        dist = drone.location.distance_from_x_y(asteroid.location.x, asteroid.location.y)

                        # ensure we didn't hit it recently (e.g. give the drone a few time steps to move away
                        # since the asteroid is only imaginary in 3D (it exists only in 2D)
                        if (dist <= (asteroid_radius + drone_radius)):
                            if ((asteroid.id not in drone.last_crash_timestep) or
                                    (self.sim_timestep - drone.last_crash_timestep[asteroid.id] >= crash_timesteps)):
                                drone.damage -= asteroid.damage
                                drone.last_crash_timestep[asteroid.id] = self.sim_timestep

        # advance the simulator timestep
        self.sim_timestep += 1
