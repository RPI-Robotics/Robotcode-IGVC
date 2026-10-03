import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from igvc_launch_utils.launch_helper import *


def generate_launch_description():
  
  # Set the path to the URDF file
  default_urdf_model_path = get_path('igvc_description', 'urdf', 'robot.urdf.xacro')

  # Launch configuration variables specific to simulation
  gui = LaunchConfiguration('gui')
  urdf_model = LaunchConfiguration('urdf_model')
  use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
  use_sim_time = LaunchConfiguration('use_sim_time')

  # Declare the launch arguments 
  launch_args = [
    DeclareLaunchArgument(
      name='urdf_model', 
      default_value=default_urdf_model_path, 
      description='Absolute path to robot urdf file'),
    
    DeclareLaunchArgument(
      name='gui',
      default_value='false',
      description='Flag to enable joint_state_publisher_gui'),
    
    DeclareLaunchArgument(
      name='use_robot_state_pub',
      default_value='true',
      description='Whether to start the robot state publisher'),

    DeclareLaunchArgument(
      name='use_sim_time',
      default_value='false',
      description='Use simulation (Gazebo) clock if true')
  ]
   
  # Specify the actions
  
  # Publish the joint state values for the non-fixed joints in the URDF file.
  start_joint_state_publisher_cmd = get_node(
    'joint_state_publisher', 
    'joint_state_publisher', 
    condition=UnlessCondition(gui))
  
  # A GUI to manipulate the joint state values
  start_joint_state_publisher_gui_node = get_node(
    'joint_state_publisher_gui',
    'joint_state_publisher_gui',
    condition=IfCondition(gui)
  )
  
  # Subscribe to the joint states of the robot, and publish the 3D pose of each link.
  start_robot_state_publisher_cmd = get_node(
    'robot_state_publisher',
    'robot_state_publisher',
    condition=IfCondition(use_robot_state_pub),
    parameters=[{'use_sim_time': use_sim_time, 
      'robot_description': Command(
        [
          'xacro ', urdf_model,
          ' use_mock_hardware:=', LaunchConfiguration('use_mock_hardware')
        ]
      ),
    }],
  )
  
  # Create foxglove bridge
  start_foxglove_bridge_cmd = get_node(
    'foxglove_bridge',
    'foxglove_bridge'
  )

  return LaunchDescription([
    *launch_args,
    start_foxglove_bridge_cmd,
    start_joint_state_publisher_cmd,
    start_joint_state_publisher_gui_node,
    start_robot_state_publisher_cmd
  ])
