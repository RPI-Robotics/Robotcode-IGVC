import rclpy
from rclpy.node import Node

from nav2_msgs.srv import ClearEntireCostmap

class CostmapClearerNode(Node):
    def __init__(self):
        super().__init__('costmap_clearer_node')
        #print msg to confirm node initialization
        self.self_logger().info("Costmap clearer node initialized.")
        
        #the following functions allow us to communicate with the local/global costmap clearing services
        #create client for clearing local costmap
        self.local_costmap_client = self.create_client(
            ClearEntireCostmap,
            "local_costmap/clear_entirely_local_costmap"
        )
        
        #create client for clearing global costmap
        self.global_costmap_client = self.create_client(
            ClearEntireCostmap,
            "global_costmap/clear_entirely_global_costmap"
        )
        
    def main(args=None):
        #initialize ros2 client library
        rclpy.init(args=args)
        
        #instantiate the node
        node = CostmapClearerNode()
        
        try:
            #repeatedly processes incoming requests on node and keeps it alive
            rclpy.spin(node)
        finally:
            #get rid of the node
            node.destroy_node()
            #shut down ros2 client library
            rclpy.shutdown()
            
    #ensure code is only run when executed directly, not when imported
    if __name__ == '__main__':
        main()
