# pytello
Python interface for the Tello.  This is an alpha version of the 
software, being released so that we can further develop it and use 
it in AI class in spring 2020.  By the end of the semester, 
the code will be in beta mode and available for general use.

# Documentation

The library is currently all in the Tello class.  To create 
a drone object, import the Tello library and create a Tello object. 

```python
from pytello.Tello import Tello

drone = Tello()
```

## Setting up the drone

Communication to the drone is done through sockets.  Before any 
flight, your program will need to tell the drone to listen 
for commands by calling connect().  At the end of a program, you 
always want to disconnect.  Forgetting
to disconnect or the program crashing before the disconnect 
can leave the socket in an odd state

* ```connect()``` -  Returns True if it succeeded and False otherwise.  It also prints out the result for the user.

* ```disconnect()``` - Closes all sockets and prints out results for the user



## Flying commands

* ```takeoff(seconds_to_wait=3)``` - takeoff and wait the specified
number of seconds before returning (to give it time to takeoff)

* ```land(seconds_to_wait=3)``` - send the land command and wait
the specified number of seconds before returning (to give it time
to land)

* ```sleep(timeout)``` - sleep for the specified time.  drone
will hover

* ```flip(direction, seconds_to_wait=3)``` - flip in the specified 
direction, which must be one of left, right, forward, back.  sleeps
for the specified time before returning to give the drone
time to flip

* ```hover(timeToHover=None)``` - tells the drone to hover for
the specified amount of time

* ```forward_cm(cm, speed=None)``` - fly forward the specified
number of cm.  cm must be in the range [20, 500].  optionally specify
a speed in cm/s in the range [10, 100].

* ```backward_cm(cm, speed=None)``` - fly backward the specified
number of cm.  cm must be in the range [20, 500].  optionally specify
a speed in cm/s in the range [10, 100].

* ```left_cm(cm, speed=None)``` - fly left the specified
number of cm.  cm must be in the range [20, 500].  optionally specify
a speed in cm/s in the range [10, 100].

* ```right_cm(cm, speed=None)``` - fly right the specified
number of cm.  cm must be in the range [20, 500].  optionally specify
a speed in cm/s in the range [10, 100].

* ```up_cm(cm, speed=None)``` - fly up the specified
number of cm.  cm must be in the range [20, 500].  optionally specify
a speed in cm/s in the range [10, 100].

* ```down_cm(cm, speed=None)``` - fly down the specified
number of cm.  cm must be in the range [20, 500].  optionally specify
a speed in cm/s in the range [10, 100].

* ```move_rectilinear_cm(x, y)``` -  move to the specified x and y 
coordinates by moving along x first and then y.  x and y are both
in the range [-500, 500] with negative x meaning backward and 
positive x meaning forward and negative y meaning left and 
positive y meaning right.

* ```fly_at_speed(x, y, z, speed)``` - fly to x, y, z all in the 
range [-500, 500] at speed in range [10,100].  Negative x means
backward and positive x means forward. Negative y means left and 
positive y means right. Negative z means down and positive z means
up.

* ```turn_degrees(degrees)``` - turn degrees in range [-360,360]. Negative
means counter-clockwise turns and positive means clockwise turns.

* ```set_speed(new_speed)``` - set a new default speed in the range
[10, 100]

## Sensors

The drone sends sensor information at 10Hz.  This is stored in
a dictionary called sensors_dict().  The full list of sensors
depends if you are in mission pad mode or not and is listed in the
SDK from Tello (see sdk_docs).  You can also call specific commands
to poll the drone.

* ```check_battery_status()``` - return the current battery status

* ```check_current_speed()``` - returns the current speed of the drone

* ```check_current_flight_time()``` - returns the total flight time

* ```check_wifi_signal()``` - check the current wifi signal

* ```check_drone_serial``` - return the drone serial number

* ```check_drone_sdk``` - check the SDK version of the drone
    

## Mission pads

The internal sensors are on by default but the drone does not
default to looking for the mission pads.  To turn that on, use
the following commands.

* ```turn_on_mission_pads()``` - this puts the drone into the mode 
to look for mission pads

* ```set_mission_pad_direction(forward, downward)``` - set
forward to True to have it look forward for pads as well
as downward.  Note that the detection rate is faster downward. You 
can set both as True as well.

* ```turn_off_mission_pads()``` - turns off mission pad detection

* ```get_visible_mission_pad_id()``` - returns the currently visible
mission pad id

* ```go_to_mission_pad_location(x, y, z, speed, mission_id)``` - moves 
the drone to the relative x, y, z location of the mission pad assuming
it is visible

# Updates
2/4/2020: Alpha release of the code for the AI class