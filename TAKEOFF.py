from Tello import Tello
import time

tello = Tello()

tello.connect()

tello.takeoff()

print("Sleeping")
tello.sleep(20)

tello.disconnect()