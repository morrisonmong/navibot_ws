import rospy
import time
import numpy as np
import os
from std_srvs.srv import Empty

from geometry_msgs.msg import Pose
from gazebo_msgs.srv import SpawnModel, SetModelState, GetPhysicsProperties
from gazebo_msgs.msg import ModelState
import subprocess



class environmentControl:
	def __init__(self, pathRobot, pathGoal, pathLaunchfile):
		self.pathRobot=pathRobot
		self.pathGoal=pathGoal
		self.goalList=np.array([[0,4,0], 
								[4,0,0],
								[-4,0,0],
								[4,4,0],
								[-4,4,0],
								[4,-4,0],
								[-4,-4,0]], dtype=float)
								# TODO: Implement proper spawn and Goal map
		self.spawnList=np.array([[ 0, 3,0],
								 [ 3, 0,0],
								 [-3, 0,0],
								 [ 3, 3,0],
								 [-3, 3,0],
								 [ 3,-3,0],
								 [-3,-3,0]], dtype=float)
		
		self.close()
		self.numGzserver=0
		#subprocess.Popen("roscore")
		#print('roscore launched')
		#time.sleep(5)
		
		subprocess.Popen(["roslaunch", pathLaunchfile])
		print('Gazebo launched')
		time.sleep(5)

		rospy.init_node('Navibot_node', anonymous=True)
		# Get Gzserver PID
		# self.gzserver_pid = int(subprocess.check_output(["pidof","-s","gzserver"]))
		
		rospy.loginfo('Waiting for service \"/gazebo/pause_physics\"... ')
		rospy.wait_for_service('/gazebo/pause_physics')
		rospy.loginfo('Waiting for service \"/gazebo/unpause_physics\"... ')
		rospy.wait_for_service('/gazebo/unpause_physics')
		rospy.loginfo('Waiting for service \"gazebo/spawn_sdf_model\"... ')
		rospy.wait_for_service('gazebo/spawn_sdf_model')
		rospy.loginfo("All services are available")
		
		self.pause_physics_client=rospy.ServiceProxy('/gazebo/pause_physics', Empty)
		self.unpause_physics_client=rospy.ServiceProxy('/gazebo/unpause_physics', Empty)
		#self.reset_simulation_client=rospy.ServiceProxy('/gazebo/reset_simulation', Empty)
		#self.reset_world_client=rospy.ServiceProxy('/gazebo/reset_world', Empty)
		self.spawn_model_client = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
		self.set_model_state_client = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
		self.physicsProp_client=rospy.ServiceProxy('gazebo/get_physics_properties', GetPhysicsProperties)

	def close(self):

		# Kill gzclient, gzserver and roscore
		tmp = os.popen("ps -Af").read()
		gzclient_count = tmp.count('gzclient')
		gzserver_count = tmp.count('gzserver')
		roscore_count = tmp.count('roscore')
		rosmaster_count = tmp.count('rosmaster')
		roslaunch_count = tmp.count('roslaunch')

		if gzclient_count > 0:
		    os.system("killall -9 gzclient")
		if gzserver_count > 0:
		    os.system("killall -9 gzserver")
		if rosmaster_count > 0:
		    os.system("killall -9 rosmaster")
		if roscore_count > 0:
		    os.system("killall -9 roscore")
		if roslaunch_count > 0:
		    os.system("killall -9 roslaunch")

		time.sleep(5)
		'''
		if (gzclient_count or gzserver_count or roscore_count or rosmaster_count >0):
		    print("I wait...")
		    os.wait()
		'''

	def pause(self):
		self.pause_physics_client.call()
	
	def unpause(self):
		self.unpause_physics_client.call()
	'''
	def reset_world(self):
		self.reset_world_client.call()

	def reset_sim(self):
		self.reset_simulation_client.call()
	'''
	def spawn(self, robotName):
		idx=np.random.randint(len(self.spawnList)-1)
		spawnPos=self.spawnList[idx]
		
		initial_pose = Pose()
		initial_pose.position.x = spawnPos[0]
		initial_pose.position.y = spawnPos[1]
		initial_pose.position.z = 0.5
		
		initial_pose.orientation.z=np.random.random()*2 -1
		initial_pose.orientation.w=np.random.random()*2 -1
		
		with open(self.pathRobot, 'r') as f:
			data=f.read()
		self.spawn_model_client(robotName, data, "naviBotNameSpace", initial_pose, "world")

	def spawnGoal(self):
		idx=np.random.randint(len(self.goalList)-1)
		goalPos=self.goalList[idx]

		goal_pose = Pose()
		goal_pose.position.x= goalPos[0]
		goal_pose.position.y= goalPos[1]
		goal_pose.position.z=2.001

		with open(self.pathGoal, 'r') as f:
			data=f.read()
		self.spawn_model_client('goal', data, "goalNameSpace", goal_pose, "world")

	def setRandomModelState(self, name):

		if name == 'goal':
			idx=np.random.randint(len(self.goalList)-1)
			goalPos=self.goalList[idx]
			
			state=ModelState()
			state.model_name=name
			state.reference_frame='world'

			state.pose.position.x = goalPos[0]
			state.pose.position.y = goalPos[1]
			state.pose.position.z = 2.001

		elif name == 'navibot':
			idx=np.random.randint(len(self.spawnList)-1)
			spawnPos=self.spawnList[idx]
			
			state=ModelState()
			state.model_name=name
			state.reference_frame='world'

			state.pose.position.x = spawnPos[0]
			state.pose.position.y = spawnPos[1]
			state.pose.position.z = 0.5

			state.pose.orientation.z = np.random.random()*2 -1
			state.pose.orientation.w = np.random.random()*2 -1

		self.set_model_state_client(state)

	def getGoallist(self):
		raise NotImplementedError()

if __name__ == '__main__':
	eC=environmentControl()
	eC.spawn('navibot')
	#eC.setRandomModelState('navibot')
	eC.setGoal()