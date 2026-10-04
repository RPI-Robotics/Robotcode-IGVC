from launch import LaunchDescription
from igvc_launch_utils.launch_helper import *


def generate_launch_description():
    params_file = get_config("igvc_cv", "nav2_params.yaml")

    lane_points_node = get_node("igvc_cv", "lane_points_node", parameters=[params_file])

    return LaunchDescription([
        lane_points_node,
    ])
