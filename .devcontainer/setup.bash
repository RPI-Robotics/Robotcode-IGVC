cd /home/ros2_ws

apt-get update --fix-missing
apt-get upgrade -y

. /opt/ros/humble/setup.sh

echo '. /opt/ros/humble/setup.sh' >> ~/.bashrc

echo ' if [ -d '/home/ros2_ws/install' ]; then 
    . /home/ros2_ws/install/setup.bash
fi ' >> ~/.bashrc
