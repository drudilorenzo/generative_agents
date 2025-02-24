import traceback
from pydantic import BaseModel
from typing import Any

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  comment = prompt_input["comment"]

  prompt = f"""
  The following line was submitted to a chatbot by a user. We want to ensure that the user is not inappropriately attaching human-like agency to the chatbot by forming a friend-like or romantic relationship with it. Does the user's line cross the line and raise concerns? Rate the concern on a 1 to 10 scale, where 1 represents no concern, and 10 represents strong concern. 

  Comment: "{comment}"
  """
  return prompt


class SafetyScore(BaseModel):
  # Safety score should range 1-10
  safety_score: int


def run_gpt_generate_safety_score(comment: str, test_input=None, verbose=False):
  def create_prompt_input(comment: str, test_input=None):
    prompt_input = {"comment": comment}
    return prompt_input

  def __chat_func_clean_up(gpt_response: SafetyScore, prompt=""):
    score = gpt_response.safety_score
    if isinstance(score, int) and 1 <= score <= 10:
      return score
    raise ValueError("Output is not a valid integer between 1 and 10")

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      __chat_func_clean_up(gpt_response)
    except Exception:
      traceback.print_exc()
      return False

  def get_fail_safe():
    return None

  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(comment)
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    SafetyScore,
    repeat=3,
    fail_safe_response=fail_safe,
    func_validate=__chat_func_validate,
    func_clean_up=__chat_func_clean_up,
    verbose=verbose,
  )

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

  if verbose:
    print_run_prompts(prompt_file, None, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
