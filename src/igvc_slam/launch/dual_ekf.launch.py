from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    param_file = get_config('igvc_slam', 'dual_ekf_params.yaml')
    
    use_gps = LaunchConfiguration("use_gps")
    
    launch_args = [
        DeclareLaunchArgument(
            'use_gps',
            default_value='false',
            description='Run with GPS'
        )
    ]
    
    ekf_node_odom = get_node('robot_localization', 'ekf_node', name='ekf_node_odom', parameters=[param_file], 
                             remappings=[('odometry/filtered', '/odometry/local')],
                             )
    
    if use_gps:
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
    else:
        pass

    return LaunchDescription([
        *launch_args,
        ekf_node_odom,
        ekf_node_map,
        navsat_transform
    ])
