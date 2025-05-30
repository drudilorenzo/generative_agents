#!/bin/bash

# Function to check if mosquitto is running
check_mosquitto_running() {
  if pgrep -x "mosquitto" >/dev/null; then
    return 0 # Mosquitto is running
  else
    return 1 # Mosquitto is not running
  fi
}

# Function to check if mosquitto is installed
check_mosquitto_installed() {
  if command -v mosquitto >/dev/null 2>&1; then
    return 0 # Mosquitto is installed
  else
    return 1 # Mosquitto is not installed
  fi
}

# Parse command line arguments
DAEMON_MODE=false
while [[ $# -gt 0 ]]; do
  case $1 in
    -d|--daemon)
      DAEMON_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [-d|--daemon]"
      exit 1
      ;;
  esac
done

# Check if mosquitto is installed
if ! check_mosquitto_installed; then
  echo "Mosquitto is not installed. Please install it first."
  exit 1
fi

# Check if mosquitto is already running
if check_mosquitto_running; then
  echo "Mosquitto is already running (PID: $(pgrep -x "mosquitto"))"
  echo "To stop it, run: pkill mosquitto"
  exit 0
fi

# Start mosquitto
if [ "$DAEMON_MODE" = true ]; then
  echo "Starting Mosquitto MQTT broker in daemon mode..."
  mosquitto -d
  
  # Wait a moment for the broker to start
  sleep 1
  
  # Check if it started successfully
  if check_mosquitto_running; then
    echo "Mosquitto started successfully (PID: $(pgrep -x "mosquitto"))"
    echo "Listening on port 1883"
    echo "To stop it, run: pkill mosquitto"
  else
    echo "Failed to start Mosquitto. Check the logs with: mosquitto -v"
    exit 1
  fi
else
  echo "Starting Mosquitto MQTT broker in attached mode..."
  echo "Press Ctrl+C to stop the broker"
  mosquitto
fi
