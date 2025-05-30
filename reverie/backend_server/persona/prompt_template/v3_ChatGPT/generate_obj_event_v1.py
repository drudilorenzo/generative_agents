import traceback
from pydantic import BaseModel
from typing import Any

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts

def create_prompt(prompt_input: dict[str, Any]):
  object = prompt_input["object"]
  persona_name = prompt_input["persona_name"]
  persona_action = prompt_input["persona_action"]

  prompt = f"""
Task: We want to understand the state of an object that is being used by someone.

Let's think step by step.
We want to know about the state of the {object}.
Step 1. {persona_name} is {persona_action}.
Step 2. Describe the state of the {object}: {object} is <fill in>
"""
  return prompt


class ObjDesc(BaseModel):
  description: str


def run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona, verbose=False):
  def create_prompt_input(act_game_object, act_desp, persona):
    prompt_input = {
      "object": act_game_object,
      "persona_name": persona.name,
      "persona_action": act_desp,
    }
    return prompt_input

  # def __func_clean_up(gpt_response, prompt=""):
  #   return ''.join(gpt_response.split("\n")[0].split(".")[0]).strip()

  # def __func_validate(gpt_response, prompt=""):
  #   try:
  #     gpt_response = __func_clean_up(gpt_response, prompt="")
  #   except:
  #     return False
  #   return True

  def get_fail_safe(act_game_object):
    fs = f"{act_game_object} is idle"
    return fs

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: ObjDesc, prompt=""):
    cr = gpt_response.description.strip()
    if cr[-1] == ".":
      cr = cr[:-1]
    return cr

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __chat_func_clean_up(gpt_response, prompt="")
    except Exception:
      traceback.print_exc()
      return False
    return True

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 200,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(act_game_object, act_desp, persona)
  prompt = create_prompt(prompt_input)
  example_output = "being fixed"
  special_instruction = "The output should ONLY contain the phrase that should go in <fill in>. It should be 15 tokens or less."
  fail_safe = get_fail_safe(act_game_object)
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    ObjDesc,
    example_output,
    special_instruction,
    3,
    fail_safe,
    __chat_func_validate,
    __chat_func_clean_up,
    True,
  )

  if verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  if output:
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================

  # gpt_param = {"engine": openai_config["model"], "max_tokens": 30,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  # prompt_template = "persona/prompt_template/v2/generate_obj_event_v1.txt"
  # prompt_input = create_prompt_input(act_game_object, act_desp, persona)
  # prompt = generate_prompt(prompt_input, prompt_template)
  # fail_safe = get_fail_safe(act_game_object)
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]
