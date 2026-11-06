import asyncio
from unittest.mock import Mock

from igvc_costmap.costmap_clearer_node import CostmapClearerNode
import pytest
import rclpy
from std_srvs.srv import Trigger


# setup method to run before each test
@pytest.fixture
def costmap_node():
    # initialize rclpy library and a costmap clearer node
    rclpy.init()
    node = CostmapClearerNode()

    # return node and pause function
    yield node

    # once function unpauses, get delete the node and shut down the library
    node.destroy_node()
    rclpy.shutdown()


def test_local_costmap_unavailable(costmap_node):
    # simulate local costmap service being unavailable
    costmap_node.local_costmap_client.service_is_ready = Mock(
        return_value=False)

    # create a request/response via the Trigger library
    request = Trigger.Request()
    response = Trigger.Response()

    # run the asynchronous callback
    result = asyncio.run(
        costmap_node.clear_costmaps_callback(
            request, response))

    # ensure correct response
    assert result.success is False
    assert result.message == 'Local costmap service unavailable'


def test_global_costmap_unavailable(costmap_node):
    # simulate local costmap service being available
    costmap_node.local_costmap_client.service_is_ready = Mock(
        return_value=True)

    # simulate global costmap service being unavailable
    costmap_node.global_costmap_client.service_is_ready = Mock(
        return_value=False)

    # create a request/response via the Trigger library
    request = Trigger.Request()
    response = Trigger.Response()

    # run the asynchronous callback
    result = asyncio.run(
        costmap_node.clear_costmaps_callback(
            request, response))

    # ensure correct response
    assert result.success is False
    assert result.message == 'Global costmap service unavailable'
