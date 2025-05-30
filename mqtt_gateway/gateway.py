import paho.mqtt.client as mqtt
import logging
import subprocess
import signal
import os
import time
from typing import Callable, Dict

from mqtt_gateway.config import (
  MQTT_BROKER_PORT,
  TOPIC_BACKEND_MOVEMENT,
  TOPIC_GATEWAY_ENVIRONMENT,
  TOPIC_GATEWAY_MOVEMENT,
  TOPIC_FRONTEND_ENVIRONMENT,
)
from mqtt_gateway.message_converter import MessageConverter


class MQTTGateway:
  def __init__(self):
    # Initialize MQTT client
    self.mqtt_client = mqtt.Client()
    self.mqtt_client.on_connect = self._on_mqtt_connect
    self.mqtt_client.on_message = self._on_mqtt_message

    # Initialize message converter
    self.converter = MessageConverter()

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    self.logger = logging.getLogger(__name__)

    # Message handlers
    self._message_handlers: Dict[str, Callable] = {
      TOPIC_BACKEND_MOVEMENT: self._handle_backend_message,
      TOPIC_FRONTEND_ENVIRONMENT: self._handle_frontend_message,
    }

    # Broker process
    self._broker_process = None

  def _start_broker(self):
    """Start the MQTT broker process."""
    try:
      # Check if mosquitto is installed
      result = subprocess.run(['mosquitto', '-h'], capture_output=True)
      if result.returncode != 0 and result.returncode != 3:
        raise Exception("mosquitto is not installed. Please install it first.")
      
      # Start mosquitto broker with configured settings
      config_path = os.path.join(os.path.dirname(__file__), "mosquitto.conf")
      logging.info(f"Starting mosquitto with config file: {config_path}")
      self._broker_process = subprocess.Popen(
        [
          "mosquitto",
          "-c",
          config_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,  # Create new process group
      )
      
      # Wait a moment for the broker to start
      time.sleep(1)
      
      if self._broker_process.poll() is None:  # Process is still running
        self.logger.info(f"MQTT broker started successfully on localhost:{MQTT_BROKER_PORT}")
      else:
        raise Exception("Failed to start MQTT broker")
        
    except subprocess.CalledProcessError:
      raise Exception("mosquitto broker is not installed. Please install it first.")
    except Exception as e:
      self.logger.error(f"Failed to start MQTT broker: {e}")
      raise

  def _stop_broker(self):
    """Stop the MQTT broker process."""
    if self._broker_process:
      try:
        # Send SIGTERM to the process group
        os.killpg(os.getpgid(self._broker_process.pid), signal.SIGTERM)
        self._broker_process.wait(timeout=5)
        self.logger.info("MQTT broker stopped successfully")
      except subprocess.TimeoutExpired:
        # If process didn't terminate gracefully, force kill it
        os.killpg(os.getpgid(self._broker_process.pid), signal.SIGKILL)
        self.logger.warning("MQTT broker was forcefully terminated")
      except Exception as e:
        self.logger.error(f"Error stopping MQTT broker: {e}")

  def start(self):
    """Start the MQTT gateway service."""
    try:
      # Start the broker first
      self._start_broker()
      
      # Connect to MQTT broker
      self.mqtt_client.connect("localhost", MQTT_BROKER_PORT)
      self.mqtt_client.loop_start()

      # Subscribe to all relevant topics
      for topic in self._message_handlers.keys():
        self.mqtt_client.subscribe(topic)
        self.logger.info(f"Subscribed to topic: {topic}")

      self.logger.info("MQTT Gateway service started successfully")

    except Exception as e:
      self.logger.error(f"Failed to start MQTT Gateway: {e}")
      self._stop_broker()  # Clean up broker if gateway fails to start
      raise

  def stop(self):
    """Stop the MQTT gateway service."""
    self.mqtt_client.loop_stop()
    self.mqtt_client.disconnect()
    self.logger.info("MQTT Gateway service stopped")
    
    # Stop the broker
    self._stop_broker()

  def _on_mqtt_connect(self, client, userdata, flags, rc):
    """Callback for MQTT connection."""
    if rc == 0:
      self.logger.info("Connected to MQTT broker")
    else:
      self.logger.error(f"Failed to connect to MQTT broker with code: {rc}")

  def _on_mqtt_message(self, client, userdata, msg):
    """Callback for MQTT messages."""
    try:
      topic = msg.topic
      payload = msg.payload.decode("utf-8")

      if topic in self._message_handlers:
        self._message_handlers[topic](payload)
      else:
        self.logger.warning(f"Received message on unknown topic: {topic}")

    except Exception as e:
      self.logger.error(f"Error processing MQTT message: {e}")

  def _handle_backend_message(self, message: str):
    """Handle messages from backend."""
    try:
      print("-----")
      logging.info(f"Received backend message: {message}")
      if self.converter.validate_message(message):
        # Convert message to frontend format
        frontend_message = self.converter.backend_to_frontend(message)
        # Publish to frontend topic
        logging.info(f"Publishing message to frontend topic: {frontend_message}")
        self.mqtt_client.publish(TOPIC_GATEWAY_MOVEMENT, frontend_message)
        self.logger.info("Converted and forwarded backend message to frontend")
    except Exception as e:
      self.logger.error(f"Error handling backend message: {e}")

  def _handle_frontend_message(self, message: str):
    """Handle messages from frontend."""
    try:
      print("-----")
      logging.info(f"Received frontend message: {message}")
      if self.converter.validate_message(message):
        # Convert message to backend format
        backend_message = self.converter.frontend_to_backend(message)
        # Publish to backend topic
        logging.info(f"Publishing message to backend topic: {backend_message}")
        self.mqtt_client.publish(TOPIC_GATEWAY_ENVIRONMENT, backend_message)
        self.logger.info("Converted and forwarded frontend message to backend")
    except Exception as e:
      self.logger.error(f"Error handling frontend message: {e}")


def main():
  gateway = MQTTGateway()

  try:
    gateway.start()
    # Keep the service running
    while True:
      pass
  except KeyboardInterrupt:
    pass
  finally:
    gateway.stop()


if __name__ == "__main__":
  main()
