from pydantic import BaseModel
import traceback
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  statements = prompt_input["statements"]
  num_insights = prompt_input["num_insights"]

  prompt = f"""
Input:
{statements}

What {num_insights} high-level insights can you infer from the above statements?
Cite the statements that support each insight by number.
(example format: {{
  "insight": "This is a high-level insight",
  "because_of": [1, 5, 3]
}})
"""
  return prompt


class Insight(BaseModel):
  insight: str
  because_of: list[int]


class InsightGuidance(BaseModel):
  insights: list[Insight]


def run_gpt_prompt_insight_and_guidance(
  persona, statements, num_insights, test_input=None, verbose=False
):
  def create_prompt_input(statements, num_insights, test_input=None):
    prompt_input = {
      "statements": statements,
      "num_insights": num_insights,
    }
    return prompt_input

  def __func_clean_up(gpt_response: InsightGuidance, prompt=""):
    ret = {item.insight: item.because_of for item in gpt_response.insights}
    return ret

  def __func_validate(gpt_response, prompt=""):
    try:
      if not isinstance(gpt_response, InsightGuidance):
        return False
      __func_clean_up(gpt_response, prompt)
      return True
    except Exception:
      traceback.print_exc()
      return False

  def get_fail_safe():
    return {"I am okay": [1, 2, 3]}

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 500,
    "temperature": 0.5,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(statements, num_insights)
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt, gpt_param, InsightGuidance, 5, fail_safe, __func_validate, __func_clean_up
  )

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
