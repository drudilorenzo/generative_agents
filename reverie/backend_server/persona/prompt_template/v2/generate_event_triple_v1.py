from pydantic import BaseModel
import traceback
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  name = prompt_input["name"]
  action = prompt_input["action"]

  prompt = f"""
Task: Turn the input into (subject, predicate, object).

Input: Sam Johnson is eating breakfast.
Output: (Sam Johnson, eat, breakfast)
---
Input: Joon Park is brewing coffee.
Output: (Joon Park, brew, coffee)
---
Input: Jane Cook is sleeping.
Output: (Jane Cook, is, sleep)
---
Input: Michael Bernstein is writing email on a computer.
Output: (Michael Bernstein, write, email)
---
Input: Percy Liang is teaching students in a classroom.
Output: (Percy Liang, teach, students)
---
Input: Merrie Morris is running on a treadmill.
Output: (Merrie Morris, run, treadmill)
---
Input: {name} is {action}.
Output:
"""
  return prompt


class EventTriple(BaseModel):
  subject: str
  predicate: str
  object: str


def run_gpt_prompt_event_triple(action_description, persona, verbose=False):
  def create_prompt_input(action_description, persona):
    if "(" in action_description:
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = {
      "name": persona.name,
      "action": action_description,
    }
    return prompt_input

  def __func_clean_up(gpt_response: EventTriple, prompt=""):
    cr = [gpt_response.predicate, gpt_response.object]
    return [x.strip() for x in cr]

  def __func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) != 2:
        return False
    except Exception:
      traceback.print_exc()
      return False
    return True

  def get_fail_safe():
    fs = ["is", "idle"]
    return fs

  # ChatGPT Plugin ===========================================================
  # def __chat_func_clean_up(gpt_response, prompt=""): ############
  #   cr = gpt_response.strip()
  #   cr = [i.strip() for i in cr.split(")")[0].split(",")]
  #   return cr

  # def __chat_func_validate(gpt_response, prompt=""): ############
  #   try:
  #     gpt_response = __func_clean_up(gpt_response, prompt="")
  #     if len(gpt_response) != 2:
  #       return False
  #   except: return False
  #   return True

  # print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 5") ########
  # gpt_param = {"engine": openai_config["model"], "max_tokens": 15,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  # prompt_template = "persona/prompt_template/v3_ChatGPT/generate_event_triple_v1.txt" ########
  # prompt_input = create_prompt_input(action_description, persona)  ########
  # prompt = generate_prompt(prompt_input, prompt_template)
  # example_output = "(Jane Doe, cooking, breakfast)" ########
  # special_instruction = "The value for the output must ONLY contain the triple. If there is an incomplete element, just say 'None' but there needs to be three elements no matter what." ########
  # fail_safe = get_fail_safe(persona) ########
  # output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 3, fail_safe,
  #                                         __chat_func_validate, __chat_func_clean_up, True)
  # if output != False:
  #   return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 200,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": ["\n"],
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(action_description, persona)
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt, gpt_param, EventTriple, 5, fail_safe, __func_validate, __func_clean_up
  )
  output = (persona.name, output[0], output[1])

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_act_obj_event_triple(
  act_game_object, act_obj_desc, persona, verbose=False
):
  def create_prompt_input(act_game_object, act_obj_desc):
    prompt_input = {
      "name": act_game_object,
      "action": act_obj_desc,
    }
    return prompt_input

  def __func_clean_up(gpt_response: EventTriple, prompt=""):
    cr = [gpt_response.predicate, gpt_response.object]
    return [x.strip() for x in cr]

  def __func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) != 2:
        return False
    except Exception:
      traceback.print_exc()
      return False
    return True

  def get_fail_safe():
    fs = ["is", "idle"]
    return fs

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 200,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": ["\n"],
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(act_game_object, act_obj_desc)
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt, gpt_param, EventTriple, 5, fail_safe, __func_validate, __func_clean_up
  )
  output = (act_game_object, output[0], output[1])

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
