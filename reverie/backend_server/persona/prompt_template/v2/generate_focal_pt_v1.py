import traceback
from typing import Any

from utils import debug
from ..common import openai_config, FocalPoint, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  statements = prompt_input["statements"]
  num_questions = prompt_input["num_questions"]

  prompt = f"""
{statements}

Given only the information above, what are the {num_questions} most salient high-level questions we can answer about the subjects in the statements?
"""
  return prompt


def run_gpt_prompt_focal_pt_v1(persona, statements, n, test_input=None, verbose=False):
  def create_prompt_input(statements, n, test_input=None):
    prompt_input = {
      "statements": statements,
      "num_questions": n,
    }
    return prompt_input

  def get_fail_safe(n):
    return ["Who am I"] * n

  def __func_clean_up(gpt_response: FocalPoint, prompt=""):
    return gpt_response.questions

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt)
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
  prompt_input = create_prompt_input(statements, n)
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe(n)
  output = safe_generate_structured_response(
    prompt, gpt_param, FocalPoint, 5, fail_safe, __func_validate, __func_clean_up
  )

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
