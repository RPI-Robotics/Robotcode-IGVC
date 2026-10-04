from launch import LaunchDescription
from igvc_launch_utils.launch_utils import *

def generate_launch_description():
    param_file = get_launch_file('igvc_slam', 'dual_ekf_params.yaml')
    
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
        ekf_node_odom,
        ekf_node_map,
        navsat_transform
    ])
