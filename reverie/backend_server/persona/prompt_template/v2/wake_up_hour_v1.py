from pydantic import BaseModel
import traceback
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  identity_stable_set = prompt_input["identity_stable_set"]
  persona_lifestyle = prompt_input["persona_lifestyle"]
  persona_firstname = prompt_input["persona_firstname"]

  prompt = f"""
{identity_stable_set}

In general, {persona_lifestyle}
{persona_firstname}'s wake up hour:
"""
  return prompt


class WakeUpHour(BaseModel):
  wake_up_hour: int


def run_gpt_prompt_wake_up_hour(persona, test_input=None, verbose=False):
  """
  Given the persona, returns an integer that indicates the hour when the
  persona wakes up.

  INPUT:
    persona: The Persona class instance
  OUTPUT:
    integer for the wake up hour.
  """

  def create_prompt_input(persona, test_input=None):
    if test_input:
      return test_input

    prompt_input = {
      "identity_stable_set": persona.scratch.get_str_iss(),
      "persona_lifestyle": persona.scratch.get_str_lifestyle(),
      "persona_firstname": persona.scratch.get_str_firstname(),
    }
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    if isinstance(gpt_response.wake_up_hour, int):
      return gpt_response.wake_up_hour
    raise TypeError("wake_up_hour of type int not found")

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt="")
    except Exception:
      traceback.print_exc()
      return False
    return True

  def get_fail_safe():
    return 8

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 100,
    "temperature": 0.8,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": ["\n"],
  }

  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(persona, test_input)
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe()

  output = safe_generate_structured_response(
    prompt, gpt_param, WakeUpHour, 5, fail_safe, __func_validate, __func_clean_up
  )

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
