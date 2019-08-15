"""
Python Tello interface based on the SDK published here:

https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf

and their example Tello3.py (which is missing many commands in the published SDK).

Some of this code was directly adapted from the pyparrot package:

https://github.com/amymcgovern/pyparrot

pytello was developed by Amy McGovern and William McGovern-Fagg
August 2019
"""

import socket
import threading
from datetime import datetime
import time

class Tello:
    def __init__(self, ip_address="192.168.10.1", port=8889):
        self.tello_address = (ip_address, port)

        self.is_listening = True

        self.sensor_dict = dict()

        self._create_udp_connection()

        # amount of time to wait in between commands (if waiting for a response)
        self.time_between_commands = 1
        self.max_command_retry_count = 3

        # start up the listener threads for state and commands (two different ports)
        self.command_response_received_status = None
        self.command_response_received = False

        self.command_listener_thread = threading.Thread(target=self._listen_command_socket)
        self.command_listener_thread.start()

        self.state_listener_thread = threading.Thread(target=self._listen_state_socket)
        self.state_listener_thread.start()


    def _create_udp_connection(self):
        """
        Create the UDP connections to the state and the command feedback
        """
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.settimeout(5.0)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.state_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.state_sock.settimeout(5.0)
        self.state_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.state_sock.bind(('0.0.0.0', 8890))
        except:
            print("Error binding to the state receive socket")

        try:
            self.sock.bind(('', 8889))
        except:
            print("Error binding to the command receive socket")


    def _listen_state_socket(self):
        """
        Listens to the socket and sleeps in between receives.
        Runs forever (until disconnect is called)
        """

        print("starting listening for state ")
        data = None

        while (self.is_listening):
            try:
                (data, address) = self.state_sock.recvfrom(1024)
                #print("state is %s" % data.decode(encoding="utf-8"))
                self.update_state(data.decode(encoding="utf-8"))

            except socket.timeout:
                #print("timeout - trying again")
                time.sleep(0.1)
                pass

            except:
                pass

        print("ending state socket listener")

    def _listen_command_socket(self):
        """
        Listens to the socket and sleeps in between receives.
        Runs forever (until disconnect is called)
        """

        print("starting listening for command feedback ")
        data = None

        while (self.is_listening):
            print("Inside loop in command listener")
            try:
                (data, address) = self.sock.recvfrom(1024)
                cmd = data.decode(encoding="utf-8")
                print("command is %s" % cmd)
                self.command_response_received = True
                self.command_response_received_status = cmd

            except socket.timeout:
                print("command socket timeout - trying again")
                time.sleep(0.1)
                pass

            except Exception as err:
                print(err)

            #self.handle_data(data)

        print("ending command socket listener")

    def update_state(self, data):
        """
        Handles the state data as it comes in.  All sensors stored in a dictionary.

        :param data: raw state data string
        :return:
        """

        sensor_readings = data.split(";")

        for i in range(0, len(sensor_readings)):
            sensor_pair = sensor_readings[i].split(':')
            try:
                self.sensor_dict[str(sensor_pair[0])] = float(sensor_pair[1])
            except:
                self.sensor_dict[str(sensor_pair[0])] = str(sensor_pair[1])

    def disconnect(self):
        """
        Disconnect cleanly from the sockets
        """
        self.is_listening = False

        # Sleep for a moment to allow all socket activity to cease before closing
        # This helps to avoids a Winsock error regarding a operations on a closed socket
        self.sleep(1)

        # then put the close in a try/except to catch any further winsock errors
        # the errors seem to be mostly occurring on windows for some reason
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception as err:
            #print(err)
            #print("Failing to shutdown the sockets")
            pass

        time.sleep(1)
        try:
            self.sock.close()
        except Exception as err:
            #print(err)
            #print("Failing to close the sockets")
            pass

        try:
            self.state_sock.shutdown(socket.SHUT_RDWR)
        except Exception as err:
            #print(err)
            #print("Failing to shutdown the state sockets")
            pass

        time.sleep(1)
        try:
            self.state_sock.close()
        except Exception as err:
            #print(err)
            #print("Failing to close the state sockets")
            pass

    def _send_command_no_wait(self, command_message):
        """
        Send the command string and wait for the response (either ok or error).
        :param command_message: the message (string)
        :return: nothing
        """
        msg = command_message.encode(encoding="utf-8")
        self.sock.sendto(msg, self.tello_address)

    def _send_command_wait_for_response(self, command_message):
        """
        Send the command string and wait for the response (either ok or error).
        :param command_message: the message (string)
        :return: True if the response was "ok" and False if it was "error"
        """
        msg = command_message.encode(encoding="utf-8")

        count = 0
        self.command_response_received = False
        while (count < self.max_command_retry_count and not self.command_response_received):
            print("sending %s" % msg)
            self.sock.sendto(msg, self.tello_address)
            self.sleep(self.time_between_commands)
            count += 1

        if (self.command_response_received_status == "ok" or self.command_response_received_status == "OK"):
            return True
        else:
            return False

    def connect(self):
        """
        Setup the Tello to be listening to SDK mode
        :return:
        """

        # initiate SDK mode
        return self._send_command_wait_for_response("command")

    def takeoff(self):
        """
        Send takeoff to the drone
        :return: True if the command was sent and False otherwise
        """
        return self._send_command_wait_for_response("takeoff")


    def land(self):
        """
        Send land to the drone
        :return: True if the command was sent and False otherwise
        """
        return self._send_command_wait_for_response("land")

    def sleep(self, timeout):
        """
        Sleeps the requested number of seconds but wakes up for notifications

        :param timeout: number of seconds to sleep
        :return:
        """

        start_time = datetime.now()
        new_time = datetime.now()
        diff = (new_time - start_time).seconds + ((new_time - start_time).microseconds / 1000000.0)

        while (diff < timeout):
            time.sleep(0.01)
            new_time = datetime.now()
            diff = (new_time - start_time).seconds + ((new_time - start_time).microseconds / 1000000.0)

    def flip(self, direction, timeToSleep):
        """
        Tell the drone to flip and then wait for the flip to happen timeToSleep seconds
        :param direction: must be one of left, right, forward, back
        :param timeToSleep: number of seconds to sleep for the flip to happen
        :return: True if the command was sent and False otherwise
        """
        if(direction is "left"):
            return self._send_command_wait_for_response("flip l")
        elif(direction is "right"):
            return self._send_command_wait_for_response("flip r")
        elif(direction is "forward"):
            return self._send_command_wait_for_response("flip f")
        elif(direction is "back"):
            return self._send_command_wait_for_response("flip b")
        else:
            print("Error: direction %s is not a valid direction.  Direction should be left, right, forward, back")
            return False

        print("flipped, sleeping now")
        self.sleep(timeToSleep)
        print("slept, exiting")

    def hover(self, timeToHover=None):
        """
        Makes the drone hover - optionally stay in hover for the time specified
        :param timeToHover: time to sleep (optional)
        :return: if it hovers or not
        """
        success = self._send_command_wait_for_response("stop")
        if (success):
            self.sleep(timeToHover)
        return success

    def _ensure_distance_within_limits(self, cm):
        """
        Internal function to ensure the distance is within the limits specified by the SDK [20,500]
        :param distance: distance in cm
        :return: the updated distance
        """
        # makes sure people aren't inputting negative numbers
        cm = abs(cm)

        #makes sure that distance is within the limits
        if (cm == 0):
            return 0

        if(cm > 0):
            if (cm < 20):
                cm = 20
            elif (cm > 500):
                cm = 500
        else:
            if (cm > -20):
                cm = -20
            elif (cm < -500):
                cm = -500

        return cm


    def forward_cm(self, cm):
        """
        Moves ONLY FORWARD in cm.  If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move FORWARDS in cm [20,500]
        :return: none
        """

        distance = self._ensure_distance_within_limits(cm)

        return self._send_command_wait_for_response("forward %03d" % distance)

    def backward_cm(self, cm):
        """
        Moves ONLY BACKWARDS in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move BACKWARDS in cm [20,500]
        :return: none
        """

        distance = self._ensure_distance_within_limits(cm)

        return self._send_command_wait_for_response("back %03d" % distance)

    def left_cm(self, cm):
        """
        Moves ONLY LEFT in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move LEFT in cm [20,500]
        :return: none
        """

        distance = self._ensure_distance_within_limits(cm)

        return self._send_command_wait_for_response("forward %03d" % distance)

    def right_cm(self, cm):
        """
        Moves ONLY RIGHT in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move RIGHT in cm [20,500]
        :return: none
        """

        distance = self._ensure_distance_within_limits(cm)

        return self._send_command_wait_for_response("back %03d" % distance)

    def move_rectilinear_cm(self, x, y):
        """
        Higher-level function to move in both x (forward/backward) and y (right/left) in straight lines.
        Moves along x first and then y.  Positive x is forward and negative x is backwards. Positive y
        is right and negative is left.

        :param pitch: the number of cms to fly forward (positive) or backward (negative).  Must be between 20 and 500
        :param roll: the number of cms to fly right (positive) or left (negative).  Must be between 20 and 500.
        :return: True if both commands succeeded and False otherwise
        """

        x = self._ensure_distance_within_limits(x)
        y = self._ensure_distance_within_limits(y)

        #making the drone move in x by sending the approprate plus or minus command
        if(x > 0):
            success1 = self.forward_cm(x)
        elif(x < 0):
            success1 = self.backward_cm(x)

        #making the drone move in y by sending the approprate plus or minus command
        if(y > 0):
            success2 = self.left_cm(y)
        elif(y < 0):
            success2 = self.right_cm(y)

        return (success1 and success2)

    def turn_degrees(self, degrees):
        """
        Turn the drone either clockwise (positive) or counterclockwise (negative)
        :param degrees: number of degrees to turn (0,360]
        :return: True if the command succeeded and False otherwise
        """

        if(degrees > 0):
            # ensure the degrees are within (0, 360]
            while(degrees > 360):
                degrees = degrees - 360

            return self._send_command_wait_for_response("cw %03d" % degrees)

        if(degrees < 0):
            # ensure the degrees are within (0, -360]
            while(degrees < -360):
                degrees = degrees + 360

            return self._send_command_wait_for_response("ccw %03d" % -degrees)

    def check_battery_status(self, safeBatt=25):
        """
        This function checks the battery percentage, returns the battery percentage and prints out if it is safe or not to fly
        :param safeBatt: the battery percentage that you want the function to print that it is not safe to takeoff at. Defaults to 25%
        :return: the battery percentage (from 0-100) if it is higher than safeBatt, and false if it is lower than safeBatt
        """

        battteryPercentage = self._send_command_wait_for_response("battery?")

        if(battteryPercentage <= safeBatt):
            print("It is not safe to takeoff!")
            return False
        else:
            print("it is safe to takeoff!")
            return battteryPercentage

    def check_current_speed(self):
        """
        Checks the current speed of the drone in cm/s
        :return: The current speed of the drone
        """

        currentSpeed = self._send_command_wait_for_response("speed?")

        return currentSpeed

    def check_current_flight_time(self):
        """
        Checks the current flight time of the drone and returns
        :return: Current flight time of the drone
        """

        currentFlightTime = self._send_command_wait_for_response("time?")

        return currentFlightTime

    def check_wifi_signal(self):
        """
        Checks the wifi signal of the drone
        :return: Wifi signal
        """

        wifiSignal = self._send_command_wait_for_response("wifi?")

        return wifiSignal

    def check_drone_serial(self):
        """
        Checks the drone's serial number
        :return: drone serial number
        """

        droneSerial = self._send_command_wait_for_response("sn?")

        return droneSerial

    def check_drone_sdk(self):
        """
        Checks the drone's sdk version
        :return: the drone sdk version
        """

        droneSDK = self._send_command_wait_for_response("sdk?")

        return droneSDK