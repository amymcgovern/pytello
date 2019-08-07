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

class Tello:
    def __init__(self, ip_address="192.168.10.1", port="8889"):
        self.tello_address = (ip_address, port)

        self.is_listening = True

        self._create_udp_connection()

        self.listener_thread = threading.Thread(target=self._listen_socket)
        self.listener_thread.start()

    def _create_udp_connection(self):
        """
        Create the UDP connection
        """
        self.udp_send_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_send_sock.bind(self.tello_address)

        self.udp_receive_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_receive_sock.settimeout(5.0)

        # re-used from pyparrot where these lines fixed errors on some machines
        self.udp_receive_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.udp_receive_sock.bind(('0.0.0.0', 8890))

    def _listen_socket(self):
        """
        Listens to the socket and sleeps in between receives.
        Runs forever (until disconnect is called)
        """

        print("starting listening at ")
        data = None

        while (self.is_listening):
            try:
                (data, address) = self.udp_receive_sock.recvfrom(1518)
                print(data.decode(encoding="utf-8"))

            except socket.timeout:
                print("timeout - trying again")

            except:
                pass

            self.handle_data(data)

        print("disconnecting", "INFO")
        self.disconnect()

    def handle_data(self, data):
        """
        Handles the data as it comes in

        :param data: raw data packet
        :return:
        """

        my_data = data

        while (my_data):
            #print("inside loop to handle data ")
            print(my_data.decode(encoding="utf-8"))


    def disconnect(self):
        """
        Disconnect cleanly from the sockets
        """
        self.is_listening = False

        # Sleep for a moment to allow all socket activity to cease before closing
        # This helps to avoids a Winsock error regarding a operations on a closed socket
        self.smart_sleep(0.5)

        # then put the close in a try/except to catch any further winsock errors
        # the errors seem to be mostly occurring on windows for some reason
        try:
            self.udp_receive_sock.close()
            self.udp_send_sock.close()
        except:
            pass

    def connect(self):
        """
        Setup the Tello to be listening to SDK mode
        :return:
        """

        # initiate SDK mode
        msg = "command".encode(encoding="utf-8")
        self.udp_send_sock.send(msg)


    def takeoff(self):
        msg = "takeoff".encode(encoding="utf-8")
        self.udp_send_sock.send(msg)


    def land(self):
        msg = "land".encode(encoding="utf-8")
        self.udp_send_sock.send(msg)
