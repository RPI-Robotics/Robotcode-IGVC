#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
class GpioEStop(Node):
    def __init__(self):
        super().__init__("gpio_estop")

        self.declare_parameter("use_sim_gpio", False)
        self.declare_parameter("sim_gpio_topic", "/sim_gpio_estop")

        self.declare_parameter("gpio_pin", 7)
        self.declare_parameter("gpio_mode", "BOARD")
        self.declare_parameter("active_high", True)

        self.declare_parameter("mechanical_estop_pin", 11)
        self.declare_parameter("mechanical_active_low", True)

        self.declare_parameter("latch", True)
        self.declare_parameter("poll_hz", 50.0)
        self.declare_parameter("lock_topic", "/emergency_stop_lock")
        self.declare_parameter("reset_topic", "/emergency_stop_reset")

        # When in sim the robot will look for sim signals, and not real ones 
        self.use_sim_gpio = self.get_parameter("use_sim_gpio").value
        self.sim_gpio_topic = self.get_parameter("sim_gpio_topic").value

        # Main e-stop pin: which pin, how pins are numbered, and whether HIGH means stop
        self.pin = self.get_parameter("gpio_pin").value
        self.mode = self.get_parameter("gpio_mode").value.upper()
        self.active_high = self.get_parameter("active_high").value

        # Mechanical e-stop pin: same idea, but active_low means LOW = stop
        self.mech_pin = self.get_parameter("mechanical_estop_pin").value
        self.mech_active_low = self.get_parameter("mechanical_active_low").value

        # latch keeps the stop on after the input clears, until a reset
        self.latch = self.get_parameter("latch").value
        self.poll_hz = float(self.get_parameter("poll_hz").value)
        self.enabled_topic = "/enabled"
        self.lock_topic = self.get_parameter("lock_topic").value
        self.reset_topic = self.get_parameter("reset_topic").value

        # This tells the robot whether the Estop is active , last_published is the last lock value sent, so we only publish when it changes
        self.estop_active = False
        self.last_published = None
        self.sim_gpio_high = False

        # Set the topic publishers for this node to be:
        #   /emergency_stop_lock
        #   /emergency_stop_reset
        #   /cmd_vel_estop
        self.enabled_pub = self.create_publisher(Bool, self.enabled_topic, 1)
        self.lock_pub = self.create_publisher(Bool, self.lock_topic, 1)
        self.estop_cmd_pub = self.create_publisher(Twist, "/cmd_vel_estop", 1)
        
        # Listens for the reset message. A True message clears the Estop
        self.reset_sub = self.create_subscription(
            Bool,
            self.reset_topic,
            self.reset_callback,
            10,
        )

        # Sets the Estop to simulation mode
        if self.use_sim_gpio:
            # Same as subscription above but for the simulation
            self.sim_gpio_sub = self.create_subscription(
                Bool,
                self.sim_gpio_topic,
                self.sim_gpio_callback,
                10,
            )

            self.GPIO = None
            self.get_logger().warn(
                f"Using sim GPIO topic: {self.sim_gpio_topic}"
            )

        # Load the pin library and set both pins as inputs 
        else:
            import Jetson.GPIO as GPIO
            self.GPIO = GPIO

            GPIO.setmode(GPIO.BOARD if self.mode == "BOARD" else GPIO.BCM)

            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.mech_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self.get_logger().info(
                f"Using Jetson GPIO pins: main={self.pin}, "
                f"mechanical={self.mech_pin}, mode={self.mode}"
            )

        # Uses the timer function to call poll_gpio function at a rate of poll_hz (default is 50Hz, so every 20ms)
        self.timer = self.create_timer(1.0 / self.poll_hz, self.poll_gpio)
        self.zero_timer = self.create_timer(0.05, self.publish_zero_cmd_if_estopped)

        self.poll_gpio()

    def sim_gpio_callback(self, msg):
        self.sim_gpio_high = msg.data

    def main_gpio_requests_estop(self):
        if self.use_sim_gpio:
            high = self.sim_gpio_high
        else:
            high = self.GPIO.input(self.pin) == self.GPIO.HIGH

        return high if self.active_high else not high

    def mechanical_gpio_requests_estop(self):
        # Mechanical e-stop only exists on real robot.
        if self.use_sim_gpio:
            return False

        high = self.GPIO.input(self.mech_pin) == self.GPIO.HIGH

        if self.mech_active_low:
            return not high
        else:
            return high

    # Simple function that returns if an Estop has been requested from any source
    def any_estop_requested(self):
        return (
            self.main_gpio_requests_estop()
            or self.mechanical_gpio_requests_estop()
        )

    # This is the most important function. This checks for Estop requests every 20ms(50Hz)
    def poll_gpio(self):
        if self.any_estop_requested():
            self.estop_active = True
        elif not self.latch:
            self.estop_active = False

        self.publish_lock(self.estop_active)
    
    # Publishes 0 to the /cmd_vel_estop topic the Estop is active
    def publish_zero_cmd_if_estopped(self):
        if self.estop_active:
            self.estop_cmd_pub.publish(Twist())

    # If there are no more estop requests, it releases the Estop, and attempts to the twist_mux for new drive commands
    def reset_callback(self, msg):
        if not msg.data:
            return

        if self.any_estop_requested():
            self.get_logger().warn(
                "Reset ignored: one or more e-stop inputs are still active."
            )
            self.estop_active = True
        else:
            self.get_logger().warn("E-stop latch reset.")
            self.estop_active = False

        self.publish_lock(self.estop_active, force=True)

    # Publishes if the estop is active and logs the data with pin number
    def publish_lock(self, locked, force=False):
        if not force and locked == self.last_published:
            return

        msg = Bool()
        msg.data = locked
        self.lock_pub.publish(msg)
        enabled_msg = Bool()
        enabled_msg.data = not locked
        self.last_published = locked

        if locked:
            self.get_logger().error(f"E-STOP ACTIVE: twist_mux locked. main={self.main_gpio_requests_estop()}, mechanical={self.mechanical_gpio_requests_estop()}")
            self.enabled_pub.publish(enabled_msg)
        else:
            self.get_logger().info(f"E-stop clear: twist_mux unlocked.")

    # Releases the pins and destroys the node
    def destroy_node(self):
        if not self.use_sim_gpio and self.GPIO is not None:
            self.GPIO.cleanup()

        super().destroy_node()

# creates the estop node and lets it run until the robot is shut down and then it destroys the node
def main(args=None):
    rclpy.init(args=args)
    node = GpioEStop()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
