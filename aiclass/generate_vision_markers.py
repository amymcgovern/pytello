import cv2
import cv2.aruco as aruco

# create the marker dictionary
aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)

num_markers = 25
for marker_id in range(1, num_markers):
    # create the marker with the specified id
    img = aruco.drawMarker(aruco_dict, marker_id, 700)

    # save the marker to a file
    cv2.imwrite("marker_%02d.png" % marker_id, img)

