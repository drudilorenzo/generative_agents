"""
MQTT client for Django frontend to handle communication with the backend.
"""

import paho.mqtt.client as mqtt
import json
from typing import Callable, Dict, Any, Union
from django.conf import settings


class MQTTConnectionError(Exception):
  """Exception raised when MQTT connection fails."""

  pass


class DjangoMQTTClient:
  _instance = None
  _client = None
  _connected = False
  _handlers = {}

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(DjangoMQTTClient, cls).__new__(cls)
    return cls._instance

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

    Raises:
        MQTTConnectionError: If connection to broker fails
    """
    if self._client is None:
      self._client = mqtt.Client(client_id=client_id)
      self._client.on_connect = self._on_connect
      self._client.on_message = self._on_message
      self._client.on_disconnect = self._on_disconnect
      self._client.on_connect_fail = self._on_connect_fail

      # Connect to broker
      try:
        self._client.connect(broker_host, broker_port)
        self._client.loop_start()
      except Exception as e:
        raise MQTTConnectionError(f"Failed to connect to MQTT broker: {e}")

      # Callback handlers
      self._handlers = {}
      self._connected = False

  def connect(self):
    """Connect to MQTT broker if not already connected."""
    client = self._get_client()
    if not self._connected:
      try:
        client.connect(
          host=settings.MQTT_BROKER_HOST, port=settings.MQTT_BROKER_PORT, keepalive=60
        )
        client.loop_start()
      except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

  def disconnect(self):
    """Disconnect from MQTT broker."""
    client = self._get_client()
    if self._connected:
      client.loop_stop()
      client.disconnect()
      self._connected = False

  def _get_client(self):
    """Get the MQTT client instance."""
    if self._client is None:
      raise MQTTConnectionError("MQTT client not initialized")
    return self._client

  def _on_connect(self, client, userdata, flags, rc):
    """Callback when connected to MQTT broker."""
    if rc == 0:
      print("Connected to MQTT broker")
      self._connected = True
    else:
      print(f"Failed to connect to MQTT broker with code: {rc}")

  def _on_disconnect(self, client, userdata, rc):
    """Callback when disconnected from MQTT broker."""
    print("Disconnected from MQTT broker")
    self._connected = False

  def _on_connect_fail(self, client, userdata):
    """Callback when MQTT connection fails."""
    print("MQTT connection failed")
    self._connected = False

  def _on_message(self, client, userdata, msg):
    """Callback when message received."""
    try:
      topic = msg.topic
      data = json.loads(msg.payload.decode())

      if topic in self._handlers:
        self._handlers[topic](data)
    except Exception as e:
      print(f"Error processing MQTT message: {e}")

  def subscribe(self, topic: str, handler: Callable):
    """Subscribe to a topic with a handler callback."""
    client = self._get_client()
    if self._connected:
      client.subscribe(topic)
      self._handlers[topic] = handler
    else:
      print("Cannot subscribe: Not connected to MQTT broker")

  def publish(self, topic: str, data: Dict[str, Any]):
    """Publish data to a topic."""
    client = self._get_client()
    if self._connected:
      client.publish(topic, json.dumps(data))
    else:
      print("Cannot publish: Not connected to MQTT broker")

  @property
  def is_connected(self) -> bool:
    """Check if client is connected to MQTT broker."""
    return self._connected
