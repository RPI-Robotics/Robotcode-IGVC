#!/usr/bin/env bash

if [ -z "$ROS_PATH" ]; then
    ROS_PATH="/opt/ros/jazzy/setup.bash"    
fi

source $ROS_PATH


if [ "$#" -lt 3 ]; then
    echo "Not enough arguments"
    echo "Need: Run method ('run' or 'launch'), package name, launch file"
    exit 1;
fi


if [ "$RUN_METHOD" == "run" ]; then
    ros2 run $PACKAGE $FILE ${OTHER[@]}

elif [ "$RUN_METHOD" == "launch" ]; then
    ros2 launch $PACKAGE $FILE ${OTHER[@]}

else
    echo "Wrong RUN_METHOD argument: Use 'run' or 'launch'"
    exit 1

fi
