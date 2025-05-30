import traceback
from typing import Any

from utils import debug
from ..common import openai_config, ConvoTakeaways, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  conversation = prompt_input["conversation"]
  persona_1_name = prompt_input["persona_1_name"]
  persona_2_name = prompt_input["persona_2_name"]

  template = f"""
[Conversation]
{conversation}
[End of conversation]

Write down if there is anything from the conversation that {persona_1_name} might have found interesting from {persona_2_name}'s perspective, in a full sentence.
Start the sentence with {persona_1_name}'s name.
"""
  return template


def run_gpt_prompt_memo_on_convo_v1(
  persona, all_utterances, test_input=None, verbose=False
):
  def create_prompt_input(persona, all_utterances, test_input=None):
    prompt_input = {
      "conversation": all_utterances,
      "persona_1_name": persona.scratch.name,
      "persona_2_name": persona.scratch.name,
    }
    return prompt_input

  def __func_clean_up(gpt_response: ConvoTakeaways, prompt=""):
    takeaways = gpt_response.takeaways.strip().strip('"')
    output = takeaways.removeprefix(persona.scratch.name).strip()
    return output

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
  prompt_input = create_prompt_input(persona, all_utterances)
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt,
    gpt_param,
    ConvoTakeaways,
    5,
    fail_safe,
    __func_validate,
    __func_clean_up,
  )

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
