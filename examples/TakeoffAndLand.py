from pytello.Tello import Tello

tello = Tello()

success = tello.connect()

if (success):
    print("Taking off!")
    tello.takeoff()

    print("Sleeping")
    tello.sleep(3)

    print("Trying to land")
    tello.land()

    tello.sleep(5)

print("Disconnecting")
tello.disconnect()