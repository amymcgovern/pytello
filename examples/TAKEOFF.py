from pytello.Tello import Tello

tello = Tello()

tello.connect()

tello.takeoff()

print("Sleeping")
tello.sleep(20)

tello.disconnect()