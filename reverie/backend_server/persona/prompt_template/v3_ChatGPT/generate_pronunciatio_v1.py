import traceback
import re
from pydantic import BaseModel
from typing import Any

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  action = prompt_input["action"]

  prompt = f"""
Convert an action description to an emoji (important: use two or fewer emojis).

Action description: {action}
Emoji:
"""
  return prompt


class Pronunciatio(BaseModel):
  emoji: str


def run_gpt_prompt_pronunciatio(action_description, persona, verbose=False):
  def create_prompt_input(action_description):
    if "(" in action_description:
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = {
      "action": action_description,
    }
    return prompt_input

  def get_fail_safe():
    return "😋"

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: Pronunciatio, prompt=""):
    # This pattern matches most modern emojis
    pattern = r"[\U0001F300-\U0001F9FF\u200d\u2600-\u26FF\u2700-\u27BF]"
    result = re.search(pattern, gpt_response.emoji)
    if result:
        return result.group()
    raise ValueError("No emoji found in the response.")

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      __chat_func_clean_up(gpt_response, prompt="")
      if len(gpt_response.emoji) == 0:
        return False
    except Exception:
      traceback.print_exc()
      return False
    return True

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
  prompt_input = create_prompt_input(action_description)
  prompt = create_prompt(prompt_input)
  example_output = "🛁🧖‍♀️"
  special_instruction = "The value for the output must ONLY contain the emojis."
  fail_safe = get_fail_safe()
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    Pronunciatio,
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

  # gpt_param = {"engine": openai_config["model"], "max_tokens": 15,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  # prompt_template = "persona/prompt_template/v2/generate_pronunciatio_v1.txt"
  # prompt_input = create_prompt_input(action_description)

  # prompt = generate_prompt(prompt_input, prompt_template)

  # fail_safe = get_fail_safe()
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]
