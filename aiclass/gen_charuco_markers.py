# Initial inspiration for this came from
# https://github.com/kyle-elsalhi/opencv-examples/blob/master/GenerateArucoMarker/GenChArucoboard.py
# creates the charuco images we can read from the wall

import cv2
import cv2.aruco as aruco

# dictionary of the marker dictionaries (needed for detection)
marker_dict = dict()
board_dict = dict()

num_markers = 25
for marker_id in range(0, num_markers):
    # create the dictionary of dictionaries so we can make a set of charuco markers
    marker_dict[marker_id] = aruco.Dictionary_create(nMarkers=25, markerSize=5, randomSeed=marker_id)

    board_dict[marker_id] = aruco.CharucoBoard_create(squaresX=5, squaresY=5, squareLength=0.06,
                                                      markerLength=0.04, dictionary=marker_dict[marker_id])

    # Create an image from the gridboard
    img = board_dict[marker_id].draw(outSize=(6400, 6400))
    cv2.imwrite("5by5by5_id%d_charuco.png" % marker_id, img)

