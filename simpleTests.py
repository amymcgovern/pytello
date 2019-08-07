from Tello import Tello
import time

tello = Tello()

tello.connect()

tello.takeoff()

time.sleep(3)

tello.land()

time.sleep(3)

tello.disconnect()