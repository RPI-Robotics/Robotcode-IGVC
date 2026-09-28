import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    config_path = config('igvc_nav', 'nav2_params.yaml')
    
    nav2 = include('nav2_bringup', 'navigation_launch.py', launch_arguments={'params_file' : config_path}.items())
    vel_scaler = include('vel_scaler', 'vel_scaler.launch.py')
    
    return LaunchDescription([
        nav2,
        vel_scaler
    ])