from nav2_msgs.srv import ClearEntireCostmap
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from std_srvs.srv import Trigger


class CostmapClearerNode(Node):
    def __init__(self):
        super().__init__('costmap_clearer_node')

        # print msg to confirm node initialization
        self.get_logger().info('Costmap clearer node initialized.')

        self.client_callback_group = ReentrantCallbackGroup()

        # the following functions allow us to communicate with existing services via a client
        # create client for clearing local costmap
        self.local_costmap_client = self.create_client(
            ClearEntireCostmap,
            'local_costmap/clear_entirely_local_costmap',
            callback_group=self.client_callback_group
        )

        # create client for clearing global costmap
        self.global_costmap_client = self.create_client(
            ClearEntireCostmap,
            'global_costmap/clear_entirely_global_costmap',
            callback_group=self.client_callback_group
        )

        # create the costmap clearing service
        self.clear_costmaps_service = self.create_service(
            Trigger, 'clear_costmaps', self.clear_costmaps_callback)

    # callback method which provides a response when this node's service is
    # called

    async def clear_costmaps_callback(self, _request, response):
        # ensure local costmap service is available
        local_success = self.local_costmap_client.service_is_ready()
        if not local_success:
            response.success = False
            response.message = 'Local costmap service unavailable'
            return response

        # ensure global costmap service is available
        global_success = self.global_costmap_client.service_is_ready()
        if not global_success:
            response.success = False
            response.message = 'Global costmap service unavailable'
            return response

        # store the clearing request in an object
        clear_request = ClearEntireCostmap.Request()

        # send the requests to Nav2 using call_async()
        local_future = self.local_costmap_client.call_async(clear_request)
        global_future = self.global_costmap_client.call_async(clear_request)

        try:
            # wait for the results of the requests
            await local_future
            await global_future
        except Exception as e:
            # handle failure as a result of an exception
            response.success = False
            response.message = 'A costmap clear request failed: ' + str(e)
            return response

        # handle success
        response.success = True
        response.message = 'Local & global costmaps successfully cleared'
        return response


def main(args=None):
    # initialize ros2 client library
    rclpy.init(args=args)

    # instantiate the node
    node = CostmapClearerNode()

    try:
        # repeatedly processes incoming requests on node and keeps it alive
        rclpy.spin(node)
    finally:
        # get rid of the node
        node.destroy_node()
        # shut down ros2 client library
        rclpy.shutdown()


# ensure code is only run when executed directly, not when imported
if __name__ == '__main__':
    main()
