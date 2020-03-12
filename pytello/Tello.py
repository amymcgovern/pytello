"""
Python Tello interface based on the SDK published here:

https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf

and their example Tello3.py (which is missing many commands in the published SDK).

Some of this code was directly adapted from the pyparrot package:

https://github.com/amymcgovern/pyparrot

pytello was developed by Amy McGovern and William McGovern-Fagg
August 2019
"""
import inspect
import socket
import threading
from datetime import datetime
import time
import cv2
import os
from os.path import join
import subprocess
from pytello.utils.NonBlockingStreamReader import NonBlockingStreamReader
from pytello.TelloVideoGUI import TelloVideoGUI

class Tello:
    def __init__(self, ip_address="192.168.10.1", port=8889, video=False, gui=False):
        # video arg added by Katy - set it to True to use video streaming
        self.tello_address = (ip_address, port)

        self.is_listening = True

        self.sensor_dict = dict()

        self._create_udp_connection()

        if gui:
            self.gui_object = TelloVideoGUI(self, None, None)
        elif video:
            self._create_video_connection()

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
                self._update_state(data.decode(encoding="utf-8"))

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

        print("ending command socket listener")

    def _update_state(self, data):
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
        print("sending no wait %s" % msg)
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
            print(self.command_response_received_status)
            return False

    def connect(self):
        """
        Setup the Tello to be listening to SDK mode

        :return: True if the connection was created and False otherwise
        """

        # initiate SDK mode
        result = self._send_command_wait_for_response("command")
        if (result):
            print("Connection successfully created")
        else:
            print("Error creating connection")
        return result

    def takeoff(self, seconds_to_wait=3):
        """
        Send takeoff to the drone

        :return: True if the command was sent and False otherwise
        """
        success = self._send_command_wait_for_response("takeoff")
        self.sleep(seconds_to_wait)
        return success


    def land(self, seconds_to_wait=3):
        """
        Send land to the drone
        :param seconds_to_wait: optional number of seconds to sleep waiting for the land to finish (default 3)
        :return: True if the command was sent and False otherwise
        """
        success = self._send_command_wait_for_response("land")
        self.sleep(seconds_to_wait)
        return success

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

    def flip(self, direction, seconds_to_wait=3):
        """
        Tell the drone to flip and then wait for the flip to happen timeToSleep seconds
        :param direction: must be one of left, right, forward, back
        :param seconds_to_wait: number of seconds to sleep for the flip to happen
        :return: True if the command was sent and False otherwise
        """
        if(direction is "left"):
            result = self._send_command_wait_for_response("flip l")
        elif(direction is "right"):
            result = self._send_command_wait_for_response("flip r")
        elif(direction is "forward"):
            result = self._send_command_wait_for_response("flip f")
        elif(direction is "back"):
            result = self._send_command_wait_for_response("flip b")
        else:
            print("Error: direction %s is not a valid direction.  Direction should be left, right, forward, back")
            return False

        # sleep the specified time
        self.sleep(seconds_to_wait)

        # return what the drone said as the flip result
        return result


    def hover(self, timeToHover=None):
        """
        Makes the drone hover - optionally stay in hover for the time specified
        :param timeToHover: time to sleep (optional)
        :return: if it hovers or not
        """
        success = self._send_command_wait_for_response("stop")
        if (success and timeToHover is not None):
            self.sleep(timeToHover)
        return success

    def _ensure_distance_within_limits(self, cm):
        """
        Internal function to ensure the distance is within the limits specified by the SDK [20,500]
        :param distance: distance in cm
        :return: the updated distance
        """

        #makes sure that distance is within the limits
        if (cm == 0):
            return 0

        # distance can't be negative in our framework
        if (cm < 0):
            cm = abs(cm)

        # ensure it is within bounds
        if (cm < 20):
            cm = 20
        elif (cm > 500):
            cm = 500

        return cm

    def _ensure_speed_within_limits(self, speed):
        """
        Internal function to ensure the distance is within the limits specified by the SDK [20,500]
        :param distance: distance in cm
        :return: the updated distance
        """
        # makes sure people aren't inputting negative numbers
        cm = abs(speed)

        if(cm >= 10):
            if (cm > 100):
                cm = 100
        else:
            # speed can't be less than 10
            return 0
        return cm


    def forward_cm(self, cm, speed=None):
        """
        Moves ONLY FORWARD in cm.  If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move FORWARDS in cm [20,500]
        :param speed: optional command to tell it to fly forward that much at a speed in the range [10,100] cm/s
        """

        distance = self._ensure_distance_within_limits(cm)

        if (speed is None):
            self._send_command_no_wait("forward %d" % distance)
        else:
            speed = self._ensure_speed_within_limits(speed)
            self._send_command_no_wait("go %d 0 0 %d" % (distance, speed))

    def backward_cm(self, cm, speed=None):
        """
        Moves ONLY BACKWARDS in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move BACKWARDS in cm [20,500]
        :param speed: optional command to tell it to fly backward that much at a speed in the range [10,100] cm/s
        """

        distance = self._ensure_distance_within_limits(cm)

        if (speed is None):
            self._send_command_no_wait("back %d" % distance)
        else:
            speed = self._ensure_speed_within_limits(speed)
            self._send_command_no_wait("go -%d 0 0 %d" % (distance, speed))

    def left_cm(self, cm, speed=None):
        """
        Moves ONLY LEFT in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move LEFT in cm [20,500]
        :param speed: optional command to tell it to fly left that much at a speed in the range [10,100] cm/s
        """

        distance = self._ensure_distance_within_limits(cm)

        if (speed is None):
            self._send_command_no_wait("left %d" % distance)
        else:
            speed = self._ensure_speed_within_limits(speed)
            self._send_command_no_wait("go 0 %d 0 %d" % (distance, speed))

    def right_cm(self, cm, speed=None):
        """
        Moves ONLY RIGHT in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move RIGHT in cm [20,500]
        :param speed: optional command to tell it to fly right that much at a speed in the range [10,100] cm/s
        """

        distance = self._ensure_distance_within_limits(cm)

        if (speed is None):
            self._send_command_no_wait("right %d" % distance)
        else:
            speed = self._ensure_speed_within_limits(speed)
            self._send_command_no_wait("go 0 -%d 0 %d" % (distance, speed))

    def up_cm(self, cm, speed=None):
        """
        Moves ONLY UP in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move UP in cm [20,500]
        :param speed: optional command to tell it to fly up that much at a speed in the range [10,100] cm/s
        """

        distance = self._ensure_distance_within_limits(cm)

        if (speed is None):
            self._send_command_no_wait("up %d" % distance)
        else:
            speed = self._ensure_speed_within_limits(speed)
            self._send_command_no_wait("go 0 0 %d %d" % (distance, speed))

    def down_cm(self, cm, speed=None):
        """
        Moves ONLY DOWN in cm. If the user gives it a negative number, the number is made positive.
        Also enforces cm between 20 and 500 (per SDK)
        :param cm: amount to move RIGHT in cm [20,500]
        :param speed: optional command to tell it to fly down that much at a speed in the range [10,100] cm/s
        """

        distance = self._ensure_distance_within_limits(cm)

        if (speed is None):
            self._send_command_no_wait("down %d" % distance)
        else:
            speed = self._ensure_speed_within_limits(speed)
            self._send_command_no_wait("go 0 0 -%d %d" % (distance, speed))

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
        else:
            # we asked it to go 0 so we assume it did just that
            success1 = True

        #making the drone move in y by sending the approprate plus or minus command
        if(y > 0):
            success2 = self.left_cm(y)
        elif(y < 0):
            success2 = self.right_cm(y)
        else:
            # we asked it to go 0 so we assume it did just that
            success2 = True

        return (success1 and success2)

    def fly_at_speed(self, x, y, z, speed):
        """
        Fly in to (x, y, z) at speed (cm/s)
        :param x: x location in cm, valid range [-500, 500] (+ forward, - backward)
        :param y: y location in cm, valid range [-500, 500] (+ right, -left)
        :param z: z location in cm, valid range [-500, 500] (+ down, - up)
        :param speed: speed in cm/s, valid range [10,100]
        :return: nothing
        """
        x = self._ensure_distance_within_limits(x)
        y = self._ensure_distance_within_limits(y)
        z = self._ensure_distance_within_limits(z)
        speed = self._ensure_speed_within_limits(speed)

        self._send_command_no_wait("go %d %d %d %d" % (x, y, z, speed))


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

            return self._send_command_wait_for_response("cw %d" % degrees)

        if(degrees < 0):
            # ensure the degrees are within (0, -360]
            while(degrees < -360):
                degrees = degrees + 360

            return self._send_command_wait_for_response("ccw %d" % -degrees)


    def turn_on_mission_pads(self):
        """
        Turn on the mission pad mode (so we detect them if we see them)

        :return: true if it succeeded and false otherwise
        """
        return self._send_command_wait_for_response("mon")

    def turn_off_mission_pads(self):
        """
        Turn off the mission pad mode (so we do not detect them if we see them)

        :return: true if it succeeded and false otherwise
        """
        return self._send_command_wait_for_response("moff")

    def set_mission_pad_direction(self, forward, downward):
        """
        Set the direction for mission pad detection.  If forward AND downward are set, it runs at 10Hz and if only one
        is set, it runs at 20Hz

        :param forward: set to True to make it look forward for pads (not sure Forward is working)
        :param downward: set to True to make it look downward for pads
        :return True if the command suceeded and False otherwise
        """
        if (downward and not forward):
            return self._send_command_wait_for_response("mdirection 0")
        elif (forward and not downward):
            return self._send_command_wait_for_response("mdirection 1")
        else:
            return self._send_command_wait_for_response("mdirection 2")

    def get_visible_mission_pad_id(self):
        """
        Return any visible mission pad ids (using sensors)
        :return: None if no mission ids are visible
        """
        if ("mid" in self.sensor_dict):
            return self.sensor_dict["mid"]
        else:
            return None

    def go_to_mission_pad_location(self, x, y, z, speed, mission_id):
        """
        Go to x, y, z in the mission pad space at specified speed.   See the mission pad manual for the diagram
        of the mission pad coordinate space
        :param x: x,y,z in range [-500, 500]
        :param y: x,y,z in range [-500, 500]
        :param z: x,y,z in range [-500, 500]
        :param speed: speed in range [10,100] cm/s
        :param mission_id: mission_id in range [1-8]
        :return:
        """
        if (x >= 0):
            x = self._ensure_distance_within_limits(x)
        else:
            x = -self._ensure_distance_within_limits(-x)

        if (y >= 0):
            y = self._ensure_distance_within_limits(y)
        else:
            y = -self._ensure_distance_within_limits(-y)

        if (z >= 0):
            z = self._ensure_distance_within_limits(z)
        else:
            z = -self._ensure_distance_within_limits(-z)

        speed = self._ensure_speed_within_limits(speed)

        return self._send_command_wait_for_response("go %d %d %d %d m%d" % (x, y, z, speed, mission_id))

    def set_speed(self, new_speed):
        """
        Set the default speed to the value specified in the range [10,100]
        :param new_speed:
        :return: True if the command suceeded and False otherwise
        """
        speed = self._ensure_speed_within_limits(new_speed)
        return self._send_command_wait_for_response("speed %d" % speed)

    def check_battery_status(self):
        """
        This returns the battery percentage

        :return: the battery percentage (from 0-100)
        """

        battteryPercentage = self._send_command_wait_for_response("battery?")
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

    ##### VIDEO STUFF
    def _create_video_connection(self):
        """prepare for video and set up buffer"""
        # set up buffer
        self.fps = 30
        self.buffer_size = 200 # default

        # initialize a buffer (will contain the last buffer_size vision objects)
        self.buffer = [None] * self.buffer_size
        self.buffer_index = 0

        # setup the thread for monitoring the vision (but don't start it until we connect in open_video)
        self.vision_thread = threading.Thread(target=self._buffer_vision,
                                              args=(self.buffer_size,))

        self.user_vision_thread = None
        self.vision_running = True

        # the vision thread starts opencv on these files.  That will happen inside the other thread
        # so here we just sent the image index to 1 ( to start)
        self.image_index = 1

        print("made it to end of create video connection")

    def set_user_callback_function(self, user_callback_function=None, user_callback_args=None):
        """
        Set the (optional) user callback function for handling the new vision frames.  This is
        run in a separate thread that starts when you start the vision buffering

        :param user_callback_function: function
        :param user_callback_args: arguments to the function
        :return:
        """
        self.user_vision_thread = threading.Thread(target=self._user_callback,
                                                   args=(user_callback_function, user_callback_args))

    def open_video(self):
        """
        Open the video stream using ffmpeg for capturing and processing.  The address for the stream
        is the same for all Mambos and is documented here:

        http://forum.developer.parrot.com/t/streaming-address-of-mambo-fpv-for-videoprojection/6442/6

        Remember that this will only work if you have connected to the wifi for your mambo!

        Note that the old method tried to open the stream directly into opencv but there are known issues
        with rtsp streams in opencv.  We bypassed opencv to use ffmpeg directly and then opencv is used to
        process the output of ffmpeg

        :return True if the vision opened correctly and False otherwise
        """
        # open video stream on drone
        self._send_command_wait_for_response("streamon")

        # we have bypassed the old opencv VideoCapture method because it was unreliable for rtsp
        # get the path for the config files
        fullPath = inspect.getfile(Tello)
        shortPathIndex = fullPath.rfind("/")
        if (shortPathIndex == -1):
            # handle Windows paths
            shortPathIndex = fullPath.rfind("\\")
        print(shortPathIndex)
        shortPath = fullPath[0:shortPathIndex]
        self.imagePath = join(shortPath, "images")
        print(self.imagePath)

        # the first step is to open the rtsp stream through ffmpeg first
        # this step creates a directory full of images, one per frame
        self.ffmpeg_process = \
                subprocess.Popen("ffmpeg -i udp://192.168.10.1:11111 -r 30 image_%03d.png &",
                                 shell=True, cwd=self.imagePath, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        # immediately start the vision buffering (before we even know if it succeeded since waiting puts us behind)
        self._start_video_buffering()

        # open non-blocking readers to look for errors or success
        print("Opening non-blocking readers")
        stderr_reader = NonBlockingStreamReader(self.ffmpeg_process.stderr)
        stdout_reader = NonBlockingStreamReader(self.ffmpeg_process.stdout)

        # look for success in the stdout
        # If it starts correctly, it will have the following output in the stdout
        # Stream mapping:
        #   Stream #0:0 -> #0:0 (h264 (native) -> png (native))

        # if it fails, it has the following in stderr
        # Output file #0 does not contain any stream

        success = False
        while (not success):

            line = stderr_reader.readline()
            if (line is not None):
                line_str = line.decode("utf-8")
                print(line_str)
                if line_str.find("Stream #0:0 -> #0:0 (h264 (native) -> png (native))") > -1:
                    success = True
                    break
                if line_str.find("Output file #0 does not contain any stream") > -1:
                    print("Having trouble connecting to the camera 1.  A reboot of the mambo may help.")
                    break

            line = stdout_reader.readline()
            if (line is not None):
                line_str = line.decode("utf-8")
                print(line_str)
                if line_str.find("Output file #0 does not contain any stream") > -1:
                    print("Having trouble connecting to the camera 2.  A reboot of the mambo may help.")
                    break

                if line_str.find("Stream #0:0 -> #0:0 (h264 (native) -> png (native))") > -1:
                    success = True

        # cleanup our non-blocking readers no matter what happened
        stdout_reader.finish_reader()
        stderr_reader.finish_reader()

        # return whether or not it worked
        return success

    def _start_video_buffering(self):
        """
        If the video capture was successfully opened, then start the thread to buffer the stream

        :return: Nothing
        """
        print("starting vision thread")
        self.vision_thread.start()

        if (self.user_vision_thread is not None):
            self.user_vision_thread.start()

    def _user_callback(self, user_vision_function, user_args):
        """
        Internal method to call the user vision functions

        :param user_vision_function: user callback function to handle vision
        :param user_args: optional arguments to the user callback function
        :return:
        """

        while (self.vision_running):
            if (self.new_frame):
                user_vision_function(user_args)

                # reset the bit for a new frame
                self.new_frame = False

            # put the thread back to sleep for fps
            # sleeping shorter to ensure we stay caught up on frames
            time.sleep(1.0 / (3.0 * self.fps))

    def _buffer_vision(self, buffer_size):
        """
        Internal method to save valid video captures from the camera fps times a second

        :param buffer_size: number of images to buffer (set in init)
        :return:
        """

        # start with no new data
        self.new_frame = False

        # when the method is first called, sometimes there is already data to catch up on
        # so find the latest image in the directory and set the index to that
        found_latest = False
        while (not found_latest):
            path = "%s/image_%03d.png" % (self.imagePath, self.image_index)
            if (os.path.exists(path)) and (not os.path.isfile(path)):
                # just increment through it (don't save any of these first images)
                self.image_index = self.image_index + 1
            else:
                found_latest = True

        # run forever, trying to grab the latest image
        while (self.vision_running):
            # grab the latest image from the ffmpeg stream
            try:
                # make the name for the next image
                path = "%s/image_%03d.png" % (self.imagePath, self.image_index)
                if (not os.path.exists(path)) and (not os.path.isfile(path)):
                    # print("File %s doesn't exist" % (path))
                    # print(os.listdir(self.imagePath))
                    continue

                img = cv2.imread(path, 1)

                # sometimes cv2 returns a None object so skip putting those in the array
                if (img is not None):
                    self.image_index = self.image_index + 1

                    # got a new image, save it to the buffer directly
                    self.buffer_index += 1
                    self.buffer_index %= buffer_size
                    # print video_frame
                    self.buffer[self.buffer_index] = img
                    self.new_frame = True

            except cv2.error:
                # Assuming its an empty image, so decrement the index and try again.
                print("Trying to read an empty png. Let's wait and try again.")
                self.image_index = self.image_index - 1
                continue

            # put the thread back to sleep for faster than fps to ensure we stay on top of the frames
            # coming in from ffmpeg
            time.sleep(1.0 / (2.0 * self.fps))

    def get_latest_valid_picture(self):
        """
        Return the latest valid image (from the buffer)

        :return: last valid image received from the Mambo
        """
        return self.buffer[self.buffer_index]

    def close_video(self):
        """
        Stop the vision processing and all its helper threads
        """

        # the helper threads look for this variable to be true
        self.vision_running = False

        # kill the ffmpeg subprocess
        self.ffmpeg_process.kill()

        self._send_command_wait_for_response("streamoff")

if __name__ == "__main__":
    tello = Tello(video=True)
    tello.connect()
    #tello.gui_object.open_video()
    tello.open_video()
    #tello.takeoff()



