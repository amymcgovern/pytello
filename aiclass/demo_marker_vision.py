"""
Example marker parsing and creation code for the AI class
Author: Amy McGovern, 07/15/2018 (original code for pyparrot library), updated to pytello 03/12/2020
"""


import cv2.aruco as aruco
import cv2
import numpy as np
from pytello.Tello import Tello
import time
from datetime import datetime

# parameters needed to make aruco vision work
aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
aruco_parameters = aruco.DetectorParameters_create()

class ArucoMarker:
    """
    Computes and holds useful information about the aruco markers
    all in a single object.  Keeps the id, the centers, the corners, and the size.
    """
    def __init__(self, corners, id):
        self.corners = corners
        self.id = id

        # calculate the center of the box
        centers = np.mean(self.corners, axis=0)
        self.center = (centers[0], centers[1])

        # compute the size of the box
        maxes = np.max(self.corners, axis=0)
        mins = np.min(self.corners, axis=0)
        self.size = (maxes[0] - mins[0]) * (maxes[1] - mins[1])

def create_aruco_markers(corner_list, ids):
    """
    Makes the aruco_marker list from the data returned from aruco.detectMarkers
    :param corner_list: list of all the corners.  Size is nx4x2 where n is the number of markers seen
    :param ids: ids for each marker
    :return: list of aruco_marker objects
    """

    if (ids is None):
        return list()

    markers = list()

    for counter, id in enumerate(ids):
        my_id = id[0]
        new_marker = ArucoMarker(np.squeeze(corner_list[counter]), my_id)
        markers.append(new_marker)

    return markers

def vision_update_markers(drone):
    """
    Called by the vision routines every time a new image comes in.  Processes images
    and looks for markers and updates all information about the markers (stored as
    global variables for ease of use across threads)

    :param args: user arguments:  first one is bebopVision
    :return: nothing
    """

    # get the latest images
    img = drone.get_latest_valid_picture()

    # if the images is invalid, return
    if(img is None):
        return

    # find markers
    corners, ids, rejectedImgPoints = aruco.detectMarkers(img, aruco_dict, parameters=aruco_parameters)
    markers = create_aruco_markers(corners, ids)

    # loop through all the markers and update the information about them
    for marker in markers:
        # you should do something with the markers you are seeing!  This is just me printing them out
        # so you see that you are detecting them and also showing them in the vision image
        print(marker.id)

    marker_img = aruco.drawDetectedMarkers(img, corners, None, borderColor=(0, 255, 0))
    return marker_img


if __name__ == "__main__":
    # make my drone object
    drone = Tello(video=True)

    # connect to the tello
    success = drone.connect(5)

    # turn on the video
    drone.open_video()

    # open a named window
    cv2.namedWindow("MarkerStream")

    # show the video for 30 seconds
    start_time = datetime.now()
    now = datetime.now()
    time_elapsed = (now - start_time).seconds
    while (time_elapsed <= 30):
        marker_img = vision_update_markers(drone)
        cv2.imshow("MarkerStream", marker_img)
        time.sleep(0.1)

        now = datetime.now()
        time_elapsed = (now - start_time).seconds

    drone.close_video()