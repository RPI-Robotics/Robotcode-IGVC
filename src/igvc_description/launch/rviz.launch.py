from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
  # Set the path to the RViz configuration settings
  default_rviz_config_path = get_config('igvc_description', 'rviz/rviz_settings.rviz')
  
  # Set the path to the URDF file
  default_urdf_model_path = get_path('igvc_description', 'urdf', 'robot.urdf.xacro')

  # Launch configuration variables specific to simulation
  gui = LaunchConfiguration('gui')
  urdf_model = LaunchConfiguration('urdf_model')
  rviz_config_file = LaunchConfiguration('rviz_config_file')
  use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
  use_rviz = LaunchConfiguration('use_rviz')
  use_sim_time = LaunchConfiguration('use_sim_time')

  # Declare the launch arguments
  launch_args = [
    DeclareLaunchArgument(
      name='urdf_model', 
      default_value=default_urdf_model_path, 
      description='Absolute path to robot urdf file'),
      
    DeclareLaunchArgument(
      name='rviz_config_file',
      default_value=default_rviz_config_path,
      description='Full path to the RVIZ config file to use'),
      
    DeclareLaunchArgument(
      name='gui',
      default_value='True',
      description='Flag to enable joint_state_publisher_gui'),
    
    DeclareLaunchArgument(
      name='use_robot_state_pub',
      default_value='True',
      description='Whether to start the robot state publisher'),

    DeclareLaunchArgument(
      name='use_rviz',
      default_value='true',
      description='Whether to start RVIZ'),
      
    DeclareLaunchArgument(
      name='use_sim_time',
      default_value='True',
      description='Use simulation (Gazebo) clock if true')
  ]
   
  # Specify the publisher action
  start_publisher_cmd = get_launch_file('igvc_description', 'publisher.launch.py', 
                                        launch_arguments={
                                          'urdf_model' : urdf_model, 
                                          'gui' : gui, 
                                          'use_robot_state_pub' : use_robot_state_pub, 
                                          'use_sim_time' : use_sim_time}.items()
                                        )

  # Launch RViz
  start_rviz_cmd = get_node("rviz2", "rviz2", condition=IfCondition(use_rviz), arguments=['-d', rviz_config_file])

  return LaunchDescription([
    #Launch options
    *launch_args,
    #Actions
    start_publisher_cmd,
    start_rviz_cmd
  ])
