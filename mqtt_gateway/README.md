# MQTT Gateway

This service acts as a message gateway between different parts of an MQTT network, handling message transformation and routing. It also manages its own MQTT broker. Use this if you need a sophistocated gateway between your simulation/backend server and your client/frontend server.

## Prerequisites

1. Python 3.9 or higher
2. mosquitto MQTT broker
   ```bash
   sudo apt-get install mosquitto
   ```

## Installation

1. Create and activate a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The gateway can be configured through environment variables in a `.env` file:

```env
MQTT_BROKER_PORT=1883
MQTT_KEEPALIVE=60
```

If not specified, the following defaults are used:
- MQTT_BROKER_PORT: 1883
- MQTT_KEEPALIVE: 60

## Running the Gateway

### From the project root directory:
```bash
python -m mqtt_gateway.gateway
```

## Topics

The gateway handles the following topics:

### Backend Communication
- `backend/movement` - Messages from backend to gateway
- `gateway/environment` - Messages from gateway to backend

### Frontend Communication
- `gateway/movement` - Messages from gateway to frontend
- `frontend/environment` - Messages from frontend to gateway

## Message Flow

1. Backend sends messages to `backend/movement`
2. Gateway receives messages, transforms them, and publishes to `gateway/movement`
3. Frontend receive messages, execute the movements, then responds on `frontend/environment`
4. Gateway receives frontend responses, transforms them, and publishes to `gateway/environment`
5. Backend receives transformed messages on `gateway/environment`

## Troubleshooting

If you encounter issues:

1. Check if mosquitto is installed and running:
   ```bash
   mosquitto -h
   ```

2. Verify the broker is running:
   ```bash
   ps aux | grep mosquitto
   ```

3. Check the gateway logs for any error messages

4. Ensure no other service is using the configured MQTT port
