from launch import LaunchDescription
from igvc_launch_utils.launch_helper import *


def generate_launch_description():
    params_file = get_config("igvc_cv", "lane_points.yaml")
    barrel_params_file = get_config("igvc_cv", "barrel_points.yaml")

    lane_points_node = get_node("igvc_cv", "lane_points_node", parameters=[params_file])
    barrel_points_node = get_node("igvc_cv", "barrel_points_node", parameters=[barrel_params_file])

    return LaunchDescription([
        lane_points_node,
        barrel_points_node,
    ])
