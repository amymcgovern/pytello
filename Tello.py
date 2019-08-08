"""
Python Tello interface based on the SDK published here:

https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf

and their example Tello3.py (which is missing many commands in the published SDK).

Some of this code was directly adapted from the pyparrot package:

https://github.com/amymcgovern/pyparrot

pytello was developed by Amy McGovern and William McGovern-Fagg
2019
"""

import socket
import threading
from datetime import datetime
import time

class Tello:
    def __init__(self, ip_address="192.168.10.1", port=8889):
        self.tello_address = (ip_address, port)

        self.is_listening = True

        self._create_udp_connection()

        # amount of time to wait in between commands (if waiting for a response)
        self.time_between_commands = 1
        self.max_command_retry_count = 3

        # start up the listener threads for state and commands (two different ports)
        self.state_listener_thread = threading.Thread(target=self._listen_state_socket)
        self.state_listener_thread.start()

        self.command_response_received_status = None
        self.command_response_received = False

        self.command_listener_thread = threading.Thread(target=self._listen_command_socket)
        self.command_listener_thread.start()

    def _create_udp_connection(self):
        """
        Create the UDP connection
        """
        self.udp_send_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        self.udp_state_receive_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_state_receive_sock.settimeout(5.0)

        self.udp_command_receive_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_command_receive_sock.settimeout(5.0)

        # re-used from pyparrot where these lines fixed errors on some machines
        self.udp_state_receive_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_command_receive_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.udp_state_receive_sock.bind(('', 8890))
        except:
            print("Error binding to the state receive socket")

        try:
            self.udp_command_receive_sock.bind(('', 9000))
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
                (data, address) = self.udp_state_receive_sock.recvfrom(1024)
                #print("state is %s" % data.decode(encoding="utf-8"))

            except socket.timeout:
                #print("timeout - trying again")
                time.sleep(0.1)
                pass

            except:
                pass

            #self.handle_data(data)

        print("ending state socket listener")

    def _listen_command_socket(self):
        """
        Listens to the socket and sleeps in between receives.
        Runs forever (until disconnect is called)
        """

        print("starting listening for command feedback ")
        data = None

        while (self.is_listening):
            try:
                (data, address) = self.udp_command_receive_sock.recvfrom(1024)
                cmd = data.decode(encoding="utf-8")
                print("command is %s" % cmd)
                self.command_response_received = True
                self.command_response_received_status = cmd

            except socket.timeout:
                #print("timeout - trying again")
                time.sleep(0.1)
                pass

            except:
                pass

            #self.handle_data(data)

        print("ending command socket listener")

    def handle_data(self, data):
        """
        Handles the data as it comes in

        :param data: raw data packet
        :return:
        """

        my_data = data

        while (my_data):
            #print("inside loop to handle data ")
            #print(my_data.decode(encoding="utf-8"))
            pass


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
            self.udp_state_receive_sock.shutdown(socket.SHUT_RDWR)
        except Exception as err:
            print(err)
            print("Failing to shutdown the sockets")

        try:
            self.udp_command_receive_sock.shutdown(socket.SHUT_RDWR)
        except Exception as err:
            print(err)
            print("Failing to shutdown the sockets")

        time.sleep(1)
        try:
            self.udp_state_receive_sock.close()
        except Exception as err:
            print(err)
            print("Failing to close the sockets")

        try:
            self.udp_command_receive_sock.close()
        except Exception as err:
            print(err)
            print("Failing to close the sockets")


    def _send_command_no_wait(self, command_message):
        """
        Send the command string and wait for the response (either ok or error).
        :param command_message: the message (string)
        :return: nothing
        """
        msg = command_message.encode(encoding="utf-8")
        self.udp_send_sock.sendto(msg, self.tello_address)

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
            self.udp_send_sock.sendto(msg, self.tello_address)
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
        Send land to the drone
        :return: True if the command was sent and False otherwise
        """
        if(direction is "left"):
            self._send_command_wait_for_response("flip l")
            self._send_command_wait_for_response("flip l")
            self._send_command_wait_for_response("flip l")
            self._send_command_wait_for_response("flip l")
            self._send_command_wait_for_response("flip l")
            return self._send_command_wait_for_response("flip l")
        elif(direction is "right"):
            self._send_command_wait_for_response("flip r")
            self._send_command_wait_for_response("flip r")
            self._send_command_wait_for_response("flip r")
            self._send_command_wait_for_response("flip r")
            self._send_command_wait_for_response("flip r")
            return self._send_command_wait_for_response("flip r")
        elif(direction is "forward"):
            self._send_command_wait_for_response("flip f")
            self._send_command_wait_for_response("flip f")
            self._send_command_wait_for_response("flip f")
            self._send_command_wait_for_response("flip f")
            self._send_command_wait_for_response("flip f")
            return self._send_command_wait_for_response("flip f")
        elif(direction is "back"):
            self._send_command_wait_for_response("flip b")
            self._send_command_wait_for_response("flip b")
            self._send_command_wait_for_response("flip b")
            self._send_command_wait_for_response("flip b")
            self._send_command_wait_for_response("flip b")
            return self._send_command_wait_for_response("flip b")

        print("flipped, sleeping now")
        self.sleep(timeToSleep)
        print("slept, exiting")

    def safe_land(self):
        """
        makes sure the dang drones lands
        :return: none
        """
        self.land()
        self.land()
        self.land()
        self.land()
        self.land()
        self.land()