from pydantic import BaseModel
import random
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  activity = prompt_input["activity"]
  available_objects = prompt_input["available_objects"]

  prompt = f"""
Current activity: sleep in bed
Objects available: [bed, easel, closet, painting]
Pick ONE most relevant object from the objects available: bed
---
Current activity: painting
Objects available: [easel, closet, sink, microwave]
Pick ONE most relevant object from the objects available: easel
---
Current activity: cooking
Objects available: [stove, sink, fridge, counter]
Pick ONE most relevant object from the objects available: stove
---
Current activity: watch TV
Objects available: [couch, TV, remote, coffee table]
Pick ONE most relevant object from the objects available: TV
---
Current activity: study
Objects available: [desk, computer, chair, bookshelf]
Pick ONE most relevant object from the objects available: desk
---
Current activity: talk on the phone
Objects available: [phone, charger, bed, nightstand]
Pick ONE most relevant object from the objects available: phone
---
Current activity: {activity}
Objects available: [{available_objects}]
Pick ONE most relevant object from the objects available:
"""
  return prompt


class GameObject(BaseModel):
  object: str


def run_gpt_prompt_action_game_object(
  action_description, persona, temp_address, test_input=None, verbose=False
):
  def create_prompt_input(action_description, persona, temp_address, test_input=None):
    if "(" in action_description:
      action_description = action_description.split("(")[-1][:-1]

    prompt_input = {
      "activity": action_description,
      "available_objects": persona.s_mem.get_str_accessible_arena_game_objects(
        temp_address
      ),
    }

    return prompt_input

  def __func_validate(gpt_response, prompt=""):
    if len(gpt_response.object.strip()) < 1:
      return False
    return True

  def __func_clean_up(gpt_response: GameObject, prompt=""):
    return gpt_response.object

  def get_fail_safe():
    fs = "<random>"
    return fs

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 100,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(
    action_description, persona, temp_address, test_input
  )
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt, gpt_param, GameObject, 5, fail_safe, __func_validate, __func_clean_up
  )

  accessible_objects = [
    i.strip()
    for i in persona.s_mem.get_str_accessible_arena_game_objects(temp_address).split(
      ","
    )
  ]
  if output not in accessible_objects:
    print("ERROR: Output is not an accessible game object:", output)
    print("Choosing a random accessible object instead.")
    output = random.choice(accessible_objects)
    print("Randomly chosen object:", output)

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
