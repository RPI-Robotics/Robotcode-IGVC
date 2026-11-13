from launch import LaunchDescription
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    config_path = get_config("igvc_nav", 'nav2_params.yaml')
    filter_config_path = get_config("igvc_nav", 'bounds_filter.yaml')

    nav2 = get_launch_file("nav2_bringup", "navigation_launch.py",
                           launch_arguments={'params_file' : config_path}.items())
    
    lidar_filter = get_node("laser_filters", "scan_to_scan_filter_chain",
                            name='lidar_filter',
                            parameters=[filter_config_path],
                            remappings=[
                                ('scan', '/scan'),
                                ('scan_filtered', '/scan_filtered'),
    ])

    return LaunchDescription([
        nav2,
        lidar_filter
    ])