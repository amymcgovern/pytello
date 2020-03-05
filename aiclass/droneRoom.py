"""
Manages the room and obstacles where the drone flies in (represents
a real room but can be used without an actual room if the drone is in simulated mode)
"""

import numpy as np

# some user defined parameters
max_velocity = 1.5 # m/s
asteroid_radius = 0.4 # in meters (this is large initially)

class Position:
    def __init__(self, x, y, orientation):
        """
        Create a new position with orientation optional

        :param x: x
        :param y: y
        :param orientation: optional orientation (needed for movement)
        """
        self.x = x
        self.y = y
        self.orientation = orientation

    def distance_from_position(self, other):
        """
        Compute the euclidean distance to the other position
        :param other:
        :return: euclidean distance
        """
        dist = np.sqrt(np.square(self.x - other.x) + np.square(self.y - other.y))
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
    def __init__(self, x, y, rotational):
        self.x = x
        self.y = y
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
            orientation = np.random.random() * np.pi * 2.0
            self.velocity = Velocity(x, y, orientation)
        else:
            self.velocity = Velocity(0, 0, 0)

class DroneRoom:
    def __init__(self, length, width, num_obstacles, num_asteroids, is_simulated):
        self.length = length
        self.width = width
        self.num_obstacles = num_obstacles
        self.num_asteroids = num_asteroids
        self.is_simulated = is_simulated
        self.asteroids = list()
        self.timestep = 0.05

        if (self.is_simulated):
            # if we are in simulation mode, automatically create the asteroid and obstacle locations
            self.__initialize_asteroids(num_obstacles, num_asteroids)
        else:
            print("Real world mode: make sure you initialize the locations for the asteroids and obstacles")

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

    def get_random_free_location(self, free_radius):
        """
        Return a random location that does not overlap any asteroids within the specified radius

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
            x = np.random.random() * self.length
            y = np.random.random() * self.width

            loc_found = True

            # make sure it is far enough away
            for asteroid in self.asteroids:
                dist = asteroid.location.distance_from_x_y(x, y)
                if (dist < free_radius or x - asteroid.radius < 0 or y - asteroid.radius < 0):
                    loc_found = False
                    break

            num_try += 1

        return Position(x, y, 0)

    def advance_time(self):
        """
        Advance time for the simulator one step

        :return:
        """

        # step one, move all the asteroids
        for asteroid in self.asteroids:
            #print(asteroid.location.x, asteroid.location.y)
            new_x = asteroid.location.x + (asteroid.velocity.x * np.cos(asteroid.velocity.rotational)) * self.timestep
            new_y = asteroid.location.y + (asteroid.velocity.y * np.sin(asteroid.velocity.rotational)) * self.timestep

            if (new_x < 0 or new_x > self.length):
                new_x = asteroid.location.x
                asteroid.velocity.x = -asteroid.velocity.x

            if (new_y < 0 or new_y > self.width):
                new_y = asteroid.location.y
                asteroid.velocity.y = -asteroid.velocity.y

            # update the location
            #print(new_x, new_y)
            asteroid.location.x = new_x
            asteroid.location.y = new_y

