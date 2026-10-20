from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    mapper_config_path = get_config('igvc_slam', 'mapper_params_online_async.yaml')
    param_file = get_config('igvc_slam', 'dual_ekf_params.yaml')
    
    use_gps = LaunchConfiguration("use_gps")
    
    launch_args = [
        DeclareLaunchArgument(
            'use_gps',
            default_value='false',
            description='Run with GPS'
        )
    ]
    
    
    slam_toolbox_launch_path = get_launch_file('slam_toolbox' , 'online_async_launch.py', 
                                            launch_arguments={
                                                'slam_params_file' : mapper_config_path,
                                                'use_sim_time' : 'false'
                                                }.items())

    return LaunchDescription([
        *launch_args,
        slam_toolbox_launch_path
    ])