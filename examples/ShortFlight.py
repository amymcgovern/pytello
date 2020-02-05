from pytello.Tello import Tello

drone = Tello()

# connect
drone.connect()

print("Taking off!")
drone.takeoff()

# fly a short distance forward
drone.forward_cm(cm=200, speed=50)
drone.sleep(3)

# flip (for fun!)
drone.flip("forward", 5)
drone.sleep(3)

# land
drone.land()

print("Disconnecting")
drone.disconnect()

print("Done")
