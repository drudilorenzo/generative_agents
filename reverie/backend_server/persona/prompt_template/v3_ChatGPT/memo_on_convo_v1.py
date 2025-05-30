import traceback
from typing import Any

from ..common import openai_config, ConvoTakeaways, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..v2.memo_on_convo_v1 import run_gpt_prompt_memo_on_convo_v1
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  identity_stable_set = prompt_input["identity_stable_set"]
  conversation = prompt_input["conversation"]
  persona_name = prompt_input["persona_name"]

  prompt = f"""
{identity_stable_set}

[Conversation]
{conversation}
[End of conversation]

Write down if there is anything from the conversation that {persona_name} might have found interesting from {persona_name}'s perspective, in a full sentence.
Start the sentence with {persona_name}'s name.
"""
  return prompt


def run_gpt_prompt_memo_on_convo(persona, all_utt, test_input=None, verbose=False):
  def create_prompt_input(persona, all_utt, test_input=None):
    prompt_input = {
      "identity_stable_set": persona.scratch.get_str_iss(),
      "conversation": all_utt,
      "persona_name": persona.scratch.name,
    }
    return prompt_input

  def get_fail_safe():
    return "..."

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: ConvoTakeaways, prompt=""):
    return gpt_response.takeaways

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      if not isinstance(gpt_response, ConvoTakeaways):
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
  prompt_input = create_prompt_input(persona, all_utt)
  prompt = create_prompt(prompt_input)
  example_output = "Jane Doe was interesting to talk to."
  special_instruction = "The output should ONLY contain a string that summarizes anything interesting that the agent may have noticed"
  fail_safe = get_fail_safe()
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    ConvoTakeaways,
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

  # Fall back to the old version
  return run_gpt_prompt_memo_on_convo_v1(persona, all_utt, test_input, verbose)
