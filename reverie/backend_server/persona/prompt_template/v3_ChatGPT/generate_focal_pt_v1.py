import traceback
from typing import Any

from ..common import openai_config, FocalPoint, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..v2.generate_focal_pt_v1 import run_gpt_prompt_focal_pt_v1
from ..print_prompt import print_run_prompts

def create_prompt(prompt_input: dict[str, Any]):
  statements = prompt_input["statements"]
  num_questions = prompt_input["num_questions"]

  prompt = f"""
{statements}

Given only the information above, what are the {num_questions} most salient high-level questions we can answer about the subjects grounded in the statements?
"""
  return prompt


def run_gpt_prompt_focal_pt(
  persona, statements, num_questions, test_input=None, verbose=False
):
  def create_prompt_input(statements, num_questions, test_input=None):
    prompt_input = {
      "statements": statements,
      "num_questions": num_questions,
    }
    return prompt_input

  def get_fail_safe(num_questions):
    return ["Who am I"] * num_questions

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: FocalPoint, prompt=""):
    ret = gpt_response.questions
    return ret

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      if not isinstance(gpt_response, FocalPoint):
        return False
      __chat_func_clean_up(gpt_response, prompt)
      return True
    except Exception:
      traceback.print_exc()
      return False

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 300,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(statements, num_questions)
  prompt = create_prompt(prompt_input)
  example_output = (
    '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
  )
  fail_safe = get_fail_safe(num_questions)
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    FocalPoint,
    example_output,
    "",
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

  # Fall back to the old version
  return run_gpt_prompt_focal_pt_v1(
    persona, statements, num_questions, test_input, verbose
  )
