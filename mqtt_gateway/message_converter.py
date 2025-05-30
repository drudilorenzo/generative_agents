import json
import logging
# import os
from mqtt_gateway.models import (
  BackendToGatewayMessage,
  FrontendToGatewayMessage,
  GatewayToFrontendMessage,
  GatewayToBackendMessage,
  AgentCommand,
  PersonaEnvironment,
  Position,
)
from mqtt_gateway.coordinate_converter import CoordinateConverter
# from mqtt_gateway.coordinate_visualizer import 

# Mock client mappings
# backend_to_frontend_mapping = {
#   "Robot 1": "Robot 1",
#   "Robot 2": "Robot 2",
#   "Robot 3": "Robot 3",
# }
# frontend_to_backend_mapping = {
#   "Robot 1": "Robot 1",
#   "Robot 2": "Robot 2",
#   "Robot 3": "Robot 3",
# }

# Real mappings
backend_to_frontend_mapping = {
  "Isabella Rodriguez": "robot_1",
  "Police Chief Rex": "non_robot",
}

frontend_to_backend_mapping = {
  "robot_1": "Isabella Rodriguez",
  "non_robot": "Police Chief Rex",
}

class MessageConverter:
  def __init__(self):
    sim_origin = (0, 0)
    sim_unit_ft = 0.784
    sim_unit_m = sim_unit_ft / 3.281

    frontend_origin_x = 61.1 / sim_unit_ft
    frontend_origin_y = 11.36 / sim_unit_ft
    frontend_origin = (frontend_origin_x, frontend_origin_y)
    frontend_unit_m = 1

    print("Creating coordinate converter")
    self.coordinate_converter = CoordinateConverter(
      source_origin=sim_origin,
      target_origin=frontend_origin,
      rotation_angle=90,
      scale_factor=frontend_unit_m / sim_unit_m,
      reflect_x=False,
      reflect_y=True,
    )
    # print("Creating coordinate visualizer")
    # self.coordinate_visualizer = CoordinateVisualizer(
    #   converter=self.coordinate_converter,
    #   background_image_path=os.path.join(
    #     os.path.dirname(__file__), "img", "sim_space.png")
    # )

    # Initialize state
    self.current_maze = "the_ville"
    self.current_step = 0

  def backend_to_frontend(self, mqtt_message: str) -> str:
    """
    Convert backend MQTT message to frontend-compatible MQTT format.
    Converts BackendToGatewayMessage to GatewayToFrontendMessage.

    Args:
        mqtt_message: JSON string from backend containing BackendToGatewayMessage

    Returns:
        JSON string in frontend-compatible format (GatewayToFrontendMessage)
    """
    try:
      backend_msg = BackendToGatewayMessage.model_validate_json(mqtt_message)
      commands = []

      # Store the current step from backend
      self.current_step = backend_msg.step

      for persona_id, movement in backend_msg.movements.persona.items():
        # Convert simulation coordinates to frontend coordinates
        sim_coords = movement.movement
        frontend_coords = self.coordinate_converter.convert_point(sim_coords)
        logging.info(f"Agent '{persona_id}': Converted sim coords {sim_coords} to frontend coords {frontend_coords}")
        # fig = self.coordinate_visualizer.plot_coordinate_transformation(
        #   source_points=[sim_coords],
        #   # target_points=[frontend_coords],
        #   title=f"Agent '{persona_id}' - Transformation",
        # )
        # fig.savefig(os.path.join(os.path.dirname(__file__), "img", f"agent_{persona_id}_transformation.png"))
        rounded_coords = (round(frontend_coords[0]), round(frontend_coords[1]))
        logging.info(f"Rounded frontend coords to {rounded_coords}")
        agent_id = backend_to_frontend_mapping[persona_id]

        command = AgentCommand(
          agent_id=agent_id,
          position=Position(x=rounded_coords[0], y=rounded_coords[1]),
        )
        commands.append(command)

      frontend_msg = GatewayToFrontendMessage(commands=commands)
      return frontend_msg.model_dump_json()

    except Exception as e:
      raise ValueError(f"Failed to convert backend message to frontend format: {e}")

  def frontend_to_backend(self, mqtt_message: str) -> str:
    """
    Convert frontend MQTT message to backend-compatible format.
    Converts FrontendToGatewayMessage to GatewayToBackendMessage.

    Args:
        mqtt_message: JSON string from frontend containing FrontendToGatewayMessage

    Returns:
        JSON string in backend-compatible format (GatewayToBackendMessage)
    """
    try:
      frontend_msg = FrontendToGatewayMessage.model_validate_json(mqtt_message)
      environment = {}

      for agent in frontend_msg.agents:
        # Convert frontend coordinates to simulation coordinates
        agent_coords = (agent.position.x, agent.position.y)
        sim_coords = self.coordinate_converter.inverse_convert_point(agent_coords)
        logging.info(f"Agent '{agent.agent_id}': Converted agent coords {agent_coords} to sim coords {sim_coords}")
        # fig = self.coordinate_visualizer.plot_inverse_transformation(
        #   target_points=[frontend_coords],
        #   # source_points=[sim_coords],
        #   title=f"Agent '{agent.agent_id}' - Inverse Transformation",
        # )
        # fig.savefig(os.path.join(os.path.dirname(__file__), "img", f"frontend_{agent.agent_id}_inverse_transformation.png"))
        rounded_coords = (round(sim_coords[0]), round(sim_coords[1]))
        logging.info(f"Rounded sim coords to {rounded_coords}")
        agent_name = frontend_to_backend_mapping[agent.agent_id]

        persona_env = PersonaEnvironment(
          x=rounded_coords[0],
          y=rounded_coords[1],
          perceived=agent.perceived,
          maze=self.current_maze,
        )
        environment[agent_name] = persona_env

      # Increment step count for the next message to backend
      next_step = self.current_step + 1

      backend_msg = GatewayToBackendMessage(
        environment=environment,
        step=next_step,
      )
      return backend_msg.model_dump_json()

    except Exception as e:
      raise ValueError(f"Failed to convert frontend message to backend format: {e}")

  @staticmethod
  def validate_message(message: str) -> bool:
    """
    Validate MQTT message format.

    Args:
        message: Message to validate

    Returns:
        True if message is valid JSON, False otherwise
    """
    try:
      json.loads(message)
      return True
    except json.JSONDecodeError:
      return False
