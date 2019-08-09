from Tello import Tello
import time

tello = Tello()

tello.connect()

tello.takeoff()
tello.sleep(8)

tello.turn_degrees(90)
tello.sleep(5)
tello.turn_degrees(-90)

tello.land()

tello.disconnect()