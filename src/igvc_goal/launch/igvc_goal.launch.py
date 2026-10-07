from launch import LaunchDescription
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    lane_director_node = get_node('igvc_goal','lane_director_node',parameters=[{'enabled_topic': '/enabled',
                                                                                'lane_points_topic': '/lanes/points',
                                                                                'base_frame': 'base_link',
                                                                                'global_frame': 'map',
                                                                                'goal_period_s': 1.0,
                                                                                'lookahead_distance_m': 3.0,
                                                                                'nominal_lane_width_m': 1.2,
                                                                                }]
                                  )
        
    return LaunchDescription([
        lane_director_node
    ])