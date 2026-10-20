import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import Command
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    igvc_slam_package = get_package_share_directory('igvc_slam')
    slam_toolbox_package  = get_package_share_directory('slam_toolbox')
    
    slam_toolbox_launch_path = os.path.join(slam_toolbox_package , 'launch', 'online_async_launch.py')
    mapper_config_path = os.path.join(igvc_slam_package, 'config', 'mapper_params_online_async.yaml')

    mapper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_toolbox_launch_path),
        launch_arguments={
            'slam_params_file' : mapper_config_path,
	    'use_sim_time' : 'false'
        }.items()
    )

    nodes = [
        mapper,
    ]

    return LaunchDescription(nodes)