FROM osrf/ros:humble-desktop
ARG USERNAME=$USERNAME
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ARG PLATFORM="LINUX"
ARG SIM_ENABLED=true
ENV SIM_ENABLED=$SIM_ENABLED

ARG DEPLOYABLE_BUILD=false

# Delete user if it exists in container (e.g Ubuntu Noble: ubuntu)
RUN if id -u $USER_UID ; then userdel `id -un $USER_UID` ; fi

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
RUN apt-get update && apt-get upgrade -y

# Unconditional installs
RUN apt-get install -y \
    python3-pip \
    ros-humble-rmw-cyclonedds-cpp 

## Simulation only
RUN if $SIM_ENABLED ; then \
        apt-get update && apt-get install -y \
            # RQT packages
            ros-humble-rqt-tf-tree ros-humble-rqt-graph ros-humble-rqt-image-view \
            # Teleop control keyboard
            ros-humble-teleop-twist-keyboard \
            # External terminal
            gnome-terminal dbus-x11 \
            # Onshape-to-robot dependencies
            openscad && \
        # Onshape-to-robot dependencies
        pip install --no-cache-dir --upgrade pip setuptools wheel && \
        pip install --no-cache-dir pybullet onshape-to-robot pymeshlab ; fi

ENV SHELL=/bin/bash

CMD ["/bin/bash"]