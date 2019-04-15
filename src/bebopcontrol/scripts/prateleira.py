import rospy
import time ## controlling the time
from geometry_msgs.msg import Twist ## controlling the velocity
import os
from alphanumeric import DetectAlphanumeric
from QrCode import QrCode
from std_msgs.msg import Empty

velocity_message = Twist()

abs_position_x = 0.0
abs_position_y = 0.0
abs_position_z = 0.0

def set_x_relative_position(x):

	'''
	Input:
	(x,y,z) = vector of position

	Task:
	publish velocity messages during the time linked to position
	'''
	global abs_position_x
	global abs_position_y
	global abs_position_z
	global velocity_message

	time_duration = abs(float(x/4))

	print(time_duration)

	timeout = time.time() + time_duration # 0.5 minutes from now

	while True:

		if x > 0:

			#print(time.time())

			velocity_message.linear.x = 4.0
			velocity_message.linear.y = 0.0
			velocity_message.linear.z = 0.0
			velocity_position_pub.publish(velocity_message)

			rate.sleep()

			if time.time() > timeout:

				#print("[ bebop2 WARN] Position reached! x: %f y: %f z: %f" % abs_position_x, abs_position_y, abs_position_z)

				return

		if x < 0:

			velocity_message.linear.x = -4.0
			velocity_message.linear.y = 0.0
			velocity_message.linear.z = 0.0
			velocity_position_pub.publish(velocity_message)

			rate.sleep()

			if time.time() > timeout:

				#print("[ bebop2 WARN] Position reached! x: %f y: %f z: %f" % abs_position_x, abs_position_y, abs_position_z)

				abs_position_x = abs_position_x + x

				return

def set_y_relative_position(y):

	'''
	Input:
	(x,y,z) = vector of position

	Task:
	publish velocity messages during the time linked to position
	'''
	global abs_position_x
	global abs_position_y
	global abs_position_z
	global velocity_message

	time_duration = abs(float(y/4))

	print(time_duration)

	timeout = time.time() + time_duration # 0.5 minutes from now

	while True:

		if y > 0:

			#print(time.time())

			velocity_message.linear.x = 0.0
			velocity_message.linear.y = 4.0
			velocity_message.linear.z = 0.0
			velocity_position_pub.publish(velocity_message)

			rate.sleep()

			if time.time() > timeout:

				#print("[ bebop2 WARN] Position reached! x: %f y: %f z: %f" % abs_position_x, abs_position_y, abs_position_z)

				return

		if y < 0:

			velocity_message.linear.x = 0.0
			velocity_message.linear.y = -4.0
			velocity_message.linear.z = 0.0
			velocity_position_pub.publish(velocity_message)

			rate.sleep()

			if time.time() > timeout:

				#print("[ bebop2 WARN] Position reached! x: %f y: %f z: %f" % abs_position_x, abs_position_y, abs_position_z)

				abs_position_y = abs_position_y + y

				return

def set_z_relative_position(z):

	'''
	Input:
	(x,y,z) = vector of position

	Task:
	publish velocity messages during the time linked to position
	'''
	global abs_position_x
	global abs_position_y
	global abs_position_z
	global velocity_message

	time_duration = abs(float(z/4))

	print(time_duration)

	timeout = time.time() + time_duration # 0.5 minutes from now

	while True:

		if z > 0:

			#print(time.time())

			velocity_message.linear.x = 0.0
			velocity_message.linear.y = 0.0
			velocity_message.linear.z = 4.0
			velocity_position_pub.publish(velocity_message)

			rate.sleep()

			if time.time() > timeout:

				#print("[ bebop2 WARN] Position reached! x: %f y: %f z: %f" % abs_position_x, abs_position_y, abs_position_z)

				return

		if z < 0:

			velocity_message.linear.x = 0.0
			velocity_message.linear.y = 0.0
			velocity_message.linear.z = -4.0
			velocity_position_pub.publish(velocity_message)

			rate.sleep()

			if time.time() > timeout:

				#print("[ bebop2 WARN] Position reached! x: %f y: %f z: %f" % abs_position_x, abs_position_y, abs_position_z)

				abs_position_z = abs_position_z + z

				return

## --- NODE --- ##

print("Welcome to the first node to control Parrot Bebop2 Drone.")
print("Developed by Skyrats Intelligent Drones team of Poli-USP.")

rospy.init_node('Bebop_2_Position_Control')

rate = rospy.Rate(20) # publish at 20 [Hz]

velocity_position_pub = rospy.Publisher('/bebop/cmd_vel', Twist, queue_size=10)
takeoff_pub = rospy.Publisher('bebop/takeoff', Empty, queue_size=1)
land_pub = rospy.Publisher('bebop/land', Empty, queue_size=1)

takeoff_pub.publish(Empty())

time.sleep(5)

print("[ bebop2 WARN] Takeoff succesfully")

alph_dec = DetectAlphanumeric()
qr_dec = QrCode()

while not rospy.is_shutdown():

	key = int(input("[ Skyrats wants to know] One more iteration?"))

	if key == 0:

		land_pub.publish(Empty())

		rospy.logwarn("Land succesfully")

	if key == 1:
		takeoff_pub.publish(Empty())
		for i in range(0, 3):

			set_y_relative_position(0.5)
			time.sleep(2)
			#rospy.loginfo('Alphanumeric Code: ' + str(alph_dec.text))
			# data = qr_dec.detect()
			# rospy.loginfo('QrCode: ' + str(data))
			rate.sleep()
