from Tello import Tello
import time

tello = Tello()

tello.connect()

tello.takeoff()

print("Sleeping")
tello.sleep(3)

print("Trying to land")
tello.land()

tello.sleep(5)

tello.disconnect()