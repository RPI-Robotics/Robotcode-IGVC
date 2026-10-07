from launch import LaunchDescription
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    single_gps_goal_node = get_node("igvc_goal", "single_gps_goal_node", parameters=[{"latitude": 42.66823105,
                                                                                      "longitude": -83.21846028,
                                                                                      "altitude": 0.0,
                                                                                      "yaw": 0.0,
                                                                                      "require_enabled": True,
                                                                                      }],
                                    )

    return LaunchDescription([
        single_gps_goal_node
    ])
