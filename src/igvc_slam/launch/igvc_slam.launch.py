from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    mapper_config_path = get_config('igvc_slam', 'mapper_params_online_async.yaml')
    
    slam_toolbox_launch_path  get_launch_file('igvc_slam' , 'online_async_launch.py', 
                                              launch_arguments={
                                                  'slam_params_file' : mapper_config_path,
                                                  'use_sim_time' : 'false'
                                                  }.items())

    return LaunchDescription([
        slam_toolbox_launch_path
    ])