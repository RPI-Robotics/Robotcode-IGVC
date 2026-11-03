import rclpy
from rclpy.node import Node

from nav2_msgs.srv import ClearEntireCostmap
from std_srvs.srv import Trigger

class CostmapClearerNode(Node):
    def __init__(self):
        super().__init__('costmap_clearer_node')
        #print msg to confirm node initialization
        self.get_logger().info("Costmap clearer node initialized.")
        
        #the following functions allow us to communicate with existing services via a client
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
        
        #create the costmap clearing service
        self.clear_costmaps_service = self.create_service(Trigger, "clear_costmaps", self.clear_costmaps_callback)
        
    #callback method which provides a response when this node's service is called
    def clear_costmaps_callback(self, request, response):
        #ensure local costmap service is available
        local_success = self.local_costmap_client.wait_for_service(timeout_sec=1.0)
        if not local_success:
            response.success = False
            response.message = "Local costmap service unavailable"
            return response
        
        #ensure global costmap service is available
        global_success = self.global_costmap_client.wait_for_service(timeout_sec=1.0)
        if not global_success:
            response.success = False
            response.message = "Global costmap service unavailable"
            return response
        
        #store the clearing request in an object
        request = ClearEntireCostmap.Request()
        
        #send the request to Nav2 using call_async() and store its return value
        local_future = self.local_costmap_client.call_async(request)
        global_future = self.global_costmap_client.call_async(request)
        
        #TODO: wait for future results and return a response accordingly
        
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
