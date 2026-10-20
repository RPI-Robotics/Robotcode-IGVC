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
    
    if use_gps != "false":
        ekf_node_odom = get_node('robot_localization', 'ekf_node', name='ekf_node_odom', parameters=[param_file], 
                            remappings=[('odometry/filtered', '/odometry/local')],
                            )
        ekf_node_map = get_node('robot_localization', 'ekf_node', name='ekf_node_map', parameters=[param_file], 
                                remappings=[('odometry/filtered', '/odometry/global')],
                                )
        navsat_transform = get_node('robot_localization', 'navsat_transform_node', name='navsat_transform', parameters=[param_file], 
                                    remappings=[
                                        ('imu', '/zed/zed_node/imu/data'), 
                                        ('gps/fix', '/fix'), 
                                        ('gps/filtered', '/gps/filtered'), 
                                        ('odometry/gps', '/odometry/gps'), 
                                        ("odometry/filtered", "/odometry/local"),
                                        ],
                                    )
        
        return LaunchDescription([
            *launch_args,
            ekf_node_odom,
            ekf_node_map,
            navsat_transform
        ])
        
    else:
        slam_toolbox_launch_path = get_launch_file('slam_toolbox' , 'online_async_launch.py', 
                                                launch_arguments={
                                                    'slam_params_file' : mapper_config_path,
                                                    'use_sim_time' : 'false'
                                                    }.items())

        return LaunchDescription([
            *launch_args,
            slam_toolbox_launch_path
        ])