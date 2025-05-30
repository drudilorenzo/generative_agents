from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel


### Backend to Gateway ###
class PersonaMovement(BaseModel):
  movement: Tuple[int, int]
  pronunciatio: str
  description: str
  chat: Optional[List[Tuple[str, str]]] = None


class Meta(BaseModel):
  curr_time: str


class Movements(BaseModel):
  persona: Dict[str, PersonaMovement]
  meta: Meta


class BackendToGatewayMessage(BaseModel):
  step: int
  movements: Movements


### Gateway to Frontend ###
class Position(BaseModel):
  x: int
  y: int


class AgentCommand(BaseModel):
  agent_id: str
  position: Position


class GatewayToFrontendMessage(BaseModel):
  commands: List[AgentCommand]


### Frontend to Gateway ###
class AgentEnvironment(BaseModel):
  agent_id: str
  position: Position
  perceived: str


class FrontendToGatewayMessage(BaseModel):
  agents: List[AgentEnvironment]


### Gateway to Backend ###
class PersonaEnvironment(BaseModel):
  x: int
  y: int
  perceived: str
  maze: str


class GatewayToBackendMessage(BaseModel):
  environment: Dict[str, PersonaEnvironment]
  step: int
