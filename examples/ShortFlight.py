from pytello.Tello import Tello

drone = Tello()

# connect
drone.connect()

print("Taking off!")
drone.takeoff()

# fly a short distance forward
drone.forward_cm(50)
drone.sleep(5)

print("Land")
drone.land()

print("Disconnecting")
drone.disconnect()

print("Done")
