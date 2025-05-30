from pydantic import BaseModel
import traceback
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  persona_name = prompt_input["persona_name"]
  thought = prompt_input["thought"]

  prompt = f"""
Translate the following thought into a statement about {persona_name}.

Thought: "{thought}"
Statement: "
"""
  return prompt


class InnerThought(BaseModel):
  thought: str


def run_gpt_prompt_generate_whisper_inner_thought(
  persona, whisper, test_input=None, verbose=False
):
  def create_prompt_input(persona, whisper, test_input=None):
    prompt_input = {
      "persona_name": persona.scratch.name,
      "thought": whisper,
    }
    return prompt_input

  def __func_clean_up(gpt_response: InnerThought, prompt=""):
    return gpt_response.thought.strip().strip('"').strip()

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt)
      return True
    except Exception:
      traceback.print_exc()
      return False

  def get_fail_safe():
    return "..."

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
  prompt_input = create_prompt_input(persona, whisper)
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt,
    gpt_param,
    InnerThought,
    5,
    fail_safe,
    __func_validate,
    __func_clean_up,
    True,
  )

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
