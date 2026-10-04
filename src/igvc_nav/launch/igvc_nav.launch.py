from launch import LaunchDescription
from igvc_launch_utils.launch_helper import *

def generate_launch_description():
    config_path = get_config("igvc_nav", 'nav2_params.yaml')

    nav2 = get_launch_file("igvc_nav", "igvc_nav.launch.py", launch_arguments={'params_file' : config_path}.items())

    return LaunchDescription([
        nav2
    ])