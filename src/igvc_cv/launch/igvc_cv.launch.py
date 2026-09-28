import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from igvc_launch_utils.launch_helper import *


def generate_launch_description():
    params_file = config("igvc_cv", "nav2_params.yaml")

    lane_points_node = node("igvc_cv", "lane_points_node", parameters=[params_file],
    )

    return LaunchDescription([
        lane_points_node,
    ])
