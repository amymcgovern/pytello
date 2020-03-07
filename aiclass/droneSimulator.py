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

# some user defined parameters
max_velocity = 1.5 # m/s
asteroid_radius = 0.4 # in meters (this is large initially)
drone_radius = 0.1 # in meters

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

        if (is_mineable):
            self.resources = np.random.random()

        if (is_moveable):
            x = np.random.random() * 2.0 * max_velocity - max_velocity
            y = np.random.random() * 2.0 * max_velocity - max_velocity
            rotational_change = (np.random.random() * 0.2) - 0.1
            self.velocity = Velocity(x, y, z=0, rotational=rotational_change)
        else:
            self.velocity = Velocity(0, 0, 0, 0)

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


class DroneSimulator:
    def __init__(self, length, width, height, num_obstacles, num_asteroids, is_simulated):
        """
        Create the empty droneRoom for flying. The user needs to add the drones (since there may be more than one
        and even more than one team)

        :param length: length of the room
        :param width: width of the room
        :param height: height of the room (if the drone exceeds this, it is "crashed" on the ground where it exceeded it
        :param num_obstacles: number of obstacles (things to not land on)
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
        self.sim_timestep = 0
        self.drones = list()

        if (self.is_simulated):
            # if we are in simulation mode, automatically create the asteroid and obstacle locations
            self.__initialize_asteroids(num_obstacles, num_asteroids)
        else:
            print("Real world mode: make sure you initialize the locations and velocities for the asteroids and obstacles and drone")

    def add_drone(self, drone):
        """
        Add the drone (simulated if we are in simulation mode and real if not) to the list of drones

        :param drone: drone object (either pyTello or a simulated pyTello)
        """
        self.drones.append(drone)

    def add_asteroid(self, position, id, is_mineable=True):
        """
        add the asteroid at the specified location to the list

        :param position: Position for the new asteroid/obstacle
        :param is_mineable: True if it is a mineable asteroid and False if it is an obstacle
        :return: nothing
        """
        if (self.is_simulated):
            is_moveable = True
        else:
            is_moveable = False

        asteroid = Asteroid(position, is_mineable, id, is_moveable)
        self.asteroids.append(asteroid)

    def __initialize_asteroids(self, num_obstacles, num_asteroids):
        """
        Create the specified number of asteroids and ensure they are in free space
        :param num_obstacles: number of obstacles e.g. non-mineable asteroids
        :param num_asteroids: number of mineable asteroids
        :return:
        """

        id = 1
        for i in range(0, num_obstacles):
            position = self.get_random_free_location(free_radius=10)
            self.add_asteroid(position, is_mineable=False, id=id)
            id+= 1

        for i in range(0, num_asteroids):
            position = self.get_random_free_location(free_radius=10)
            self.add_asteroid(position, is_mineable=True, id=id)
            id+=1

    def add_random_simulated_drone(self, id, team_color):
        """
        Creates a new drone in a random location

        :return the random drone
        """
        position = self.get_random_free_location(free_radius=10)
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
        max_tries = 5
        loc_found = False

        x = 0
        y = 0

        while (num_try < max_tries and not loc_found):
            # try again
            x = np.random.random() * (self.length - free_radius)
            y = np.random.random() * (self.width - free_radius)

            loc_found = True

            # make sure it is far enough away
            for asteroid in self.asteroids:
                dist = asteroid.location.distance_from_x_y(x, y)
                if (dist < free_radius or x - free_radius < 0 or y - free_radius < 0):
                    loc_found = False
                    break

            num_try += 1

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
            #print(asteroid.location.x, asteroid.location.y)
            new_x = asteroid.location.x + (asteroid.velocity.x * np.cos(asteroid.location.orientation)) * self.physics_timestep
            new_y = asteroid.location.y + (asteroid.velocity.y * np.sin(asteroid.location.orientation)) * self.physics_timestep
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
            new_x = drone.location.x + (drone.velocity.x * np.cos(drone.location.orientation)) * self.physics_timestep
            new_y = drone.location.y + (drone.velocity.y * np.sin(drone.location.orientation)) * self.physics_timestep
            new_z = drone.location.z + (drone.velocity.z * self.physics_timestep)
            new_angle = drone.location.orientation + (drone.velocity.rotational * self.physics_timestep)
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
            #print(new_x, new_y, new_z)
            drone.location.x = new_x
            drone.location.y = new_y
            drone.location.z = new_z
            drone.location.orientation = new_angle

        # advance the simulator timestep
        self.sim_timestep += 1