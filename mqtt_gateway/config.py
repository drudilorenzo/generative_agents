import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MQTT Configuration
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', "broker.example.com")
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))

# Topics
# Backend communication
TOPIC_BACKEND_MOVEMENT = "backend/movement"
TOPIC_GATEWAY_ENVIRONMENT = "gateway/environment"

# Frontend communication
TOPIC_GATEWAY_MOVEMENT = "gateway/movement"
TOPIC_FRONTEND_ENVIRONMENT = "frontend/environment"
