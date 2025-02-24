from pydantic import BaseModel
from enum import IntEnum
import traceback
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  context = prompt_input["context"]
  curr_time = prompt_input["curr_time"]
  init_persona_action_and_place = prompt_input["init_persona_action_and_place"]
  target_persona_action_and_place = prompt_input["target_persona_action_and_place"]
  init_persona_name = prompt_input["init_persona_name"]
  init_persona_action = prompt_input["init_persona_action"]
  target_persona_name = prompt_input["target_persona_name"]
  target_persona_action = prompt_input["target_persona_action"]

  prompt = f"""
Task -- Given context and two options that a subject can take, determine which option is the most acceptable and provide your reasoning.

Context: Jane is Liz's house mate. Jane and Liz exchanged a conversation about saying good morning at 07:05am, October 25, 2022.
Right now, it is 07:09 am, October 25, 2022.
Jane was on her way to using the bathroom right now.
Jane sees Liz already using the bathroom.
My question: Let's think step by step. Of the following two options, what should Jane do?
Option 1: Wait on using the bathroom until Liz is done using the bathroom
Option 2: Continue on to using the bathroom now

Reasoning: Both Jane and Liz want to use the bathroom.
It would be strange for both Jane and Liz to use the bathroom at the same time.
So, since Liz is already using the bathroom, the best option for Jane is to wait on using the bathroom.
Answer: 1
---
Context: Sam is Sarah's friend. Sam and Sarah exchanged a conversation about favorite movies at 11pm, October 24, 2022.
Right now, it is 12:40 pm, October 25, 2022.
Sam is on the way to study for his test.
Sam sees Sarah heading to do her laundry.
My question: Let's think step by step. Of the following two options, what should Sam do?
Option 1: Wait on eating his lunch until Sarah is done doing her laundry
Option 2: Continue on to eating his lunch now

Reasoning: Sam is likely going to be in his room studying. Sarah, on the other hand, is likely headed to the laundry room for doing the laundry.
Since Sam and Sarah need to use different areas, their actions do not conflict.
So, since Sam and Sarah are going to be in different areas, Sam can continue on to eating his lunch now.
Answer: 2
---
Context: {context}
Right now, it is {curr_time}.
{init_persona_action_and_place}
{target_persona_action_and_place}
My question: Let's think step by step. Of the following two options, what should {init_persona_name} do?
Option 1: Wait on {init_persona_action} until {target_persona_name} is done {target_persona_action}
Option 2: Continue on to {init_persona_action} now
"""
  return prompt


class DecideToReactEnum(IntEnum):
  one = 1
  two = 2


class DecideToReact(BaseModel):
  reasoning: str
  decision: DecideToReactEnum


def run_gpt_prompt_decide_to_react(
  persona,
  target_persona,
  retrieved,
  test_input=None,
  verbose=False,
):
  def create_prompt_input(init_persona, target_persona, retrieved, test_input=None):
    context = ""
    for c_node in retrieved["events"]:
      curr_desc = c_node.description.split(" ")
      curr_desc[2:3] = ["was"]
      curr_desc = " ".join(curr_desc)
      context += f"{curr_desc}. "
    context += "\n"
    for c_node in retrieved["thoughts"]:
      context += f"{c_node.description}. "

    curr_time = init_persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
    init_persona_action = init_persona.scratch.act_description
    if "(" in init_persona_action:
      init_persona_action = init_persona_action.split("(")[-1][:-1]
    if len(init_persona.scratch.planned_path) == 0:
      loc = ""
      if ":" in init_persona.scratch.act_address:
        loc = (
          init_persona.scratch.act_address.split(":")[-1]
          + " in "
          + init_persona.scratch.act_address.split(":")[-2]
        )
      init_persona_action_and_place = (
        f"{init_persona.name} is already {init_persona_action} at {loc}"
      )
    else:
      loc = ""
      if ":" in init_persona.scratch.act_address:
        loc = (
          init_persona.scratch.act_address.split(":")[-1]
          + " in "
          + init_persona.scratch.act_address.split(":")[-2]
        )
      init_persona_action_and_place = (
        f"{init_persona.name} is on the way to {init_persona_action} at {loc}"
      )

    target_persona_action = target_persona.scratch.act_description
    if "(" in target_persona_action:
      target_persona_action = target_persona_action.split("(")[-1][:-1]
    if len(target_persona.scratch.planned_path) == 0:
      loc = ""
      if ":" in target_persona.scratch.act_address:
        loc = (
          target_persona.scratch.act_address.split(":")[-1]
          + " in "
          + target_persona.scratch.act_address.split(":")[-2]
        )
      target_persona_action_and_place = (
        f"{target_persona.name} is already {target_persona_action} at {loc}"
      )
    else:
      loc = ""
      if ":" in target_persona.scratch.act_address:
        loc = (
          target_persona.scratch.act_address.split(":")[-1]
          + " in "
          + target_persona.scratch.act_address.split(":")[-2]
        )
      target_persona_action_and_place = (
        f"{target_persona.name} is on the way to {target_persona_action} at {loc}"
      )

    prompt_input = {
      "context": context,
      "curr_time": curr_time,
      "init_persona_action_and_place": init_persona_action_and_place,
      "target_persona_action_and_place": target_persona_action_and_place,
      "init_persona_name": init_persona.name,
      "init_persona_action": init_persona_action,
      "target_persona_name": target_persona.name,
      "target_persona_action": target_persona_action,
    }

    return prompt_input

  def __func_validate(gpt_response: DecideToReact, prompt=""):
    try:
      if gpt_response.decision.value in [1, 2]:
        return True
      return False
    except Exception:
      traceback.print_exc()
      return False

  def __func_clean_up(gpt_response: DecideToReact, prompt=""):
    return str(gpt_response.decision.value)

  def get_fail_safe():
    fs = "3"
    return fs

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 1000,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(persona, target_persona, retrieved, test_input)
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt,
    gpt_param,
    DecideToReact,
    5,
    fail_safe,
    __func_validate,
    __func_clean_up,
  )
  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
