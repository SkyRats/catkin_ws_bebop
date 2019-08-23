#!/usr/bin/env python
import rospy
import numpy as np
import math

from geometry_msgs.msg import PoseStamped, TwistStamped, Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64, Empty
from std_srvs.srv import Trigger, TriggerRequest, TriggerResponse, SetBool, SetBoolRequest, SetBoolResponse
from bebop_msgs.msg import Ardrone3PilotingStateAltitudeChanged

from dronecontrol.msg import Vector3D
from PID import PID

from dynamic_reconfigure.server import Server
from dronecontrol.cfg import ControlConfig

import time


class vso_controler(object): # visual odometry drone controler
    
    goal_pose = np.array([0.0,0.0,1.0])
    current_pose = np.array([0.0,0.0,0.0])
    offset_pose = np.array([0.0,0.0,0.0])
    offset_vel = np.array([0.0,0.0,0.0])
    angle_pose = 0.0
    scale_factor = 1.0
    pid_x = PID(P=rospy.get_param('P_x', '2.0'),I=rospy.get_param('I_x', '0.0'),D=rospy.get_param('D_x', '0.0'))
    pid_y = PID(P=rospy.get_param('P_y', '2.0'),I=rospy.get_param('I_y', '0.0'),D=rospy.get_param('D_y', '0.0'))
    pid_z = PID(P=rospy.get_param('P_z', '2.0'),I=rospy.get_param('I_z', '0.0'),D=rospy.get_param('D_z', '0.0'))


    camera_angle = Twist()
    setted_vel = Twist()
    adjusted_vel = Twist()

    vso_on = False            # visual odometry based control status
    control_mode = "position" # position or velocity  
    trust_vso = 1
    last_vso_time = 0 

    def __init__(self):

        #setup node
        rospy.init_node('Vel_Control_Node', anonymous=True)
        self.rate = rospy.Rate(60)  # refresh rate (Hz)

        #topics and services
        self.setpoint_velocity_pub = rospy.Publisher('/bebop/cmd_vel', Twist, queue_size=1)
        self.camera_angle_pub = rospy.Publisher('/bebop/camera_control', Twist, queue_size=10)


        rospy.Subscriber('/orb_slam2_mono/pose', PoseStamped, self.vso_position_callback)
        rospy.Subscriber('/bebop/states/ardrone3/PilotingState/AltitudeChanged', Ardrone3PilotingStateAltitudeChanged, self.altitude_callback)
        rospy.Subscriber('/bebop/odom/', Odometry, self.odometry_callback)
        rospy.Subscriber('/bebop/land', Empty, self.land)
        rospy.Subscriber('/bebop/takeoff', Empty, self.takeoff)

        rospy.Subscriber('/control/position', Vector3D, self.position_callback)
        rospy.Subscriber('/control/velocity', Vector3D, self.velocity_callback)
        rospy.Subscriber('/control/rotation', Float64, self.rotation_callback)
        # rospy.Subscriber('/control/land', Empty, self.land)

        #turn on and of the viual odometry based control
        rospy.Service('/control/set_vso', SetBool, self.set_vso_handle)
        rospy.Service('/control/reset_vso_coords', Trigger , self.reset_vso_position_service)

        #dynamic parameters serve
        srv = Server(ControlConfig, self.parameters_callback)
        
        t = time.time()
        rospy.loginfo("aligning camera")
        while time.time() - t < 3:
            self.align_camera()

        rospy.loginfo("setup ok")

    # ------------ topics callbacks -----------
    def land(self,callback_data):
        self.vso_on = False
    def takeoff(self,callback_data):
        self.align_camera()
        # reset_vso_position()
        # self.vso_on = True
    def rotation_callback(self):
        pass
    def altitude_callback(self,altitude):
        # rospy.loginfo("altitude: ")
        # rospy.loginfo(altitude.altitude)
        pass
    def odometry_callback(self, odom):
        # rospy.loginfo("odom: ")
        self.angle_pose = odom.pose.pose.orientation.z
        if rospy.get_time() - self.last_vso_time > 0.5:
            self.trust_vso = 0
            rospy.loginfo("NO FEATURES!!!")


    def position_callback(self, goal_vec):    
        self.goal_pose[0] = goal_vec.x
        self.goal_pose[1] = goal_vec.y
        self.goal_pose[2] = goal_vec.z

        self.pid_x.setPoint(self.goal_pose[0])
        self.pid_y.setPoint(self.goal_pose[1])
        self.pid_z.setPoint(self.goal_pose[2])

        self.control_mode = "position"
        # rospy.loginfo("got a goal position: ")
        

    def velocity_callback(self, goal_vec):
        self.setted_vel.linear.z = goal_vec.z
        self.setted_vel.linear.y = goal_vec.y
        self.setted_vel.linear.x = goal_vec.x

        self.control_mode = "velocity"
        rospy.loginfo("got velocity goal")
        # rospy.loginfo("VELOCITY: x: " + str(goal_vec.x) + " y: " +
        #             str(goal_vec.y) + " z: " + str(goal_vec.z))

    def vso_position_callback(self,pose):
        self.trust_vso = 1
        self.last_vso_time = rospy.get_time()
        self.current_pose[0] = self.scale_factor*pose.pose.position.x - self.offset_pose[0]
        self.current_pose[1] = self.scale_factor*pose.pose.position.y - self.offset_pose[1]
        self.current_pose[2] = self.scale_factor*pose.pose.position.z - self.offset_pose[2]
        rospy.loginfo("POSE: x: " + str(self.current_pose[0]) + " y: " +
                    str(self.current_pose[1]) + " z: " + str(self.current_pose[2]))
        
        
        self.offset_vel[0] = self.pid_x.update(self.current_pose[0])
        self.offset_vel[1] = self.pid_y.update(self.current_pose[1])
        self.offset_vel[2] = self.pid_z.update(self.current_pose[2])

        rospy.loginfo("VELOCITY: x: " + str(self.offset_vel[0]) + " y: " + str(self.offset_vel[1]) + " z: " + str(self.offset_vel[2]))
        
        # print(self.offset_vel)

    def parameters_callback(self, config, level):
        rospy.loginfo("""Reconfigure Request: \n P_x {P_x} I_x {I_x} D_x {D_x} \n P_y {P_y} I_y {I_y} D_y {D_y} \n P_z {P_z} I_z {I_z} D_z {D_z} \n scale_factor {scale_factor} \n off_x {offset_pose_x} off_y {offset_pose_y} off_z {offset_pose_z} \n vso_on {vso_on}""".format(**config))
        if hasattr(self, 'pid_x'):
            self.pid_x.set_PID_constants(config.P_x,config.I_x,config.D_x)
            self.pid_y.set_PID_constants(config.P_y,config.I_y,config.D_y)
            self.pid_z.set_PID_constants(config.P_z,config.I_z,config.D_z)
        else:
            self.pid_x = PID(P=config.P_x,I=config.I_x,D=config.D_x)
            self.pid_y = PID(P=config.P_y,I=config.I_y,D=config.D_y)
            self.pid_z = PID(P=config.P_z,I=config.I_z,D=config.D_z)

        self.scale_factor = config.scale_factor
        self.vso_on = config.vso_on
        # self.offset_pose[0] = config.offset_pose_x
        # self.offset_pose[1] = config.offset_pose_y
        # self.offset_pose[2] = config.offset_pose_z
        return config
    # ------- service handles ----------
    def set_vso_handle(self, request):
        assert isinstance(request, SetBoolRequest)
        self.vso_on = request.data
        return SetBoolResponse(True, "New vso running status is: {}".format(""))
    def reset_vso_position_service(self, request):
        assert isinstance(request, TriggerRequest)
        try:
            self.reset_vso_position()    
            return TriggerResponse(True, "vso coordenate system reseted for the current position")
        except:
            return TriggerResponse(False, "Reset Failed")
    def reset_vso_position(self):
        self.offset_pose += self.current_pose
        self.current_pose = np.array([0.0,0.0,0.0])
        self.goal_pose -= self.current_pose
        
        self.pid_x.setPoint(self.goal_pose[0])
        self.pid_y.setPoint(self.goal_pose[1])
        self.pid_z.setPoint(self.goal_pose[2])
        self.pid_x.update(self.current_pose[0])
        self.pid_y.update(self.current_pose[1])
        self.pid_z.update(self.current_pose[2])


    # ------ control methods -----------
    def align_camera(self):
        self.camera_angle.angular.x = 0
        self.camera_angle.angular.y = 3
        self.camera_angle.angular.z = 0
        self.camera_angle_pub.publish(self.camera_angle)
    def adjust_vel(self):
        self.adjusted_vel.linear.z = self.setted_vel.linear.z + self.offset_vel[2]
        self.adjusted_vel.linear.y = self.setted_vel.linear.y + self.offset_vel[1]
        self.adjusted_vel.linear.x = self.setted_vel.linear.x + self.offset_vel[0]


    def run(self):
        while not rospy.is_shutdown():
            if self.vso_on and self.control_mode == "position" and self.trust_vso:
                self.adjust_vel()
            else:
                self.adjusted_vel = self.setted_vel

            self.setpoint_velocity_pub.publish(self.adjusted_vel)
            
            self.rate.sleep()


if __name__ == "__main__":
    c = vso_controler()
    c.run()
