"""
MQTT client for handling communication between frontend and backend.
"""

import paho.mqtt.client as mqtt
import json
from typing import Callable, Dict, Any, Union


class ReverieMQTTClient:
  def __init__(
    self,
    broker_host: str = "localhost",
    broker_port: int = 1883,
    client_id: Union[str, None] = None,
  ):
    """Initialize the MQTT client.

    Args:
        broker_host: MQTT broker host address
        broker_port: MQTT broker port
        client_id: Unique client ID for this instance
    """
    self.client = mqtt.Client(client_id=client_id)
    self.client.on_connect = self._on_connect
    self.client.on_message = self._on_message

    # Connect to broker
    self.client.connect(broker_host, broker_port)
    self.client.loop_start()

    # Callback handlers
    self._handlers: Dict[str, Callable] = {}

  def _on_connect(self, client, userdata, flags, rc):
    """Callback when connected to MQTT broker."""
    print(f"Connected to MQTT broker with result code {rc}")

  def _on_message(self, client, userdata, msg):
    """Callback when message received."""
    try:
      data = json.loads(msg.payload.decode())
      topic = msg.topic

      # Call registered handler if exists
      if topic in self._handlers:
        self._handlers[topic](data)

    except Exception as e:
      print(f"Error processing message: {e}")

  def subscribe(self, topic: str, handler: Callable):
    """Subscribe to a topic with a handler callback.

    Args:
        topic: MQTT topic to subscribe to
        handler: Callback function to handle messages
    """
    self.client.subscribe(topic)
    self._handlers[topic] = handler

  def unsubscribe(self, topic: str):
    """Unsubscribe from a topic.

    Args:
        topic: MQTT topic to unsubscribe from
    """
    self.client.unsubscribe(topic)

  def publish(self, topic: str, data: Dict[str, Any]):
    """Publish data to a topic.

    Args:
        topic: MQTT topic to publish to
        data: Data to publish (will be JSON encoded)
    """
    self.client.publish(topic, json.dumps(data))

  def close(self):
    """Close the MQTT client connection."""
    self.client.loop_stop()
    self.client.disconnect()
