import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def include(package, launch_file, **kwargs):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(package), '/launch/', *launch_file]),
        **kwargs
    )

def generate_launch_description():
    config_path = LaunchConfiguration('config_path')
    
    launch_args = [
        DeclareLaunchArgument(
            'config_path',
            default_value=PathJoinSubstitution([FindPackageShare('igvc_nav'), 'config', 'nav2_params.yaml']),
            description='Navigation configuration path'
        ),
    ] 
    
    nav2 = include('nav2_bringup', 'navigation_launch.py', launch_arguments={'params_file' : config_path}.items())
    vel_scaler = include('vel_scaler', 'vel_scaler.launch.py')
    
    
    return LaunchDescription([
        *launch_args,
        nav2,
        vel_scaler
    ])