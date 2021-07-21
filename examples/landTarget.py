from pytello.Tello import Tello

drone = Tello()

# connect
drone.connect()
print("Connected!")

# target mission pad
target_pad_id = 3

# start flying
drone.takeoff()

drone.up_cm(100)
drone.sleep(5)

# fly forward slowly looking for the pad
tries = 1
max_tries = 20
while (drone.get_visible_mission_pad_id() != target_pad_id and tries < max_tries):
    print("Looking for mission pad")
    drone.forward_cm(50)
    drone.sleep(3)
    tries += 1

print("flipping")
drone.flip(direction="left")
print("flipped")

# if we found the right pad (and still see it), go to the middle of it
mission_id = drone.get_visible_mission_pad_id()
if (mission_id == target_pad_id):
    print("Found pad %d" % mission_id)
    success = drone.go_to_mission_pad_location(0, 0, 40, 20, mission_id)
    print(success)
    drone.sleep(2)

# land
drone.land()

print("Disconnecting")
drone.disconnect()

print("Done")
