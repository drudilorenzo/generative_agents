import traceback
from pydantic import BaseModel
from typing import Any

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  conversation = prompt_input["conversation"]
  persona_name = prompt_input["persona_name"]

  prompt = f"""
[Conversation]
{conversation}
[End of conversation]

Summarize the conversation above in one sentence, using {persona_name} as the subject.
Start the sentence with "{persona_name} is talking to"
"""
  return prompt


class ConversationSummary(BaseModel):
  summary: str


def run_gpt_prompt_summarize_conversation(
  persona, conversation, test_input=None, verbose=False
):
  def create_prompt_input(conversation, test_input=None):
    convo_str = ""
    for row in conversation:
      convo_str += f'{row[0]}: "{row[1]}"\n'

    prompt_input = {
      "conversation": convo_str,
      "persona_name": persona.scratch.name,
    }
    return prompt_input

  # def __func_clean_up(gpt_response: ConversationSummary, prompt=""):
  #   ret = "conversing about " + gpt_response.conversation.strip()
  #   return ret

  # def __func_validate(gpt_response, prompt=""):
  #   try:
  #     __func_clean_up(gpt_response, prompt)
  #     return True
  #   except:
  #     traceback.print_exc()
  #     return False

  def get_fail_safe():
    return "talking to a housemate about morning greetings"

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: ConversationSummary, prompt=""):
    stripped_summary = (
      gpt_response.summary.strip()
      .strip(".")
      .removeprefix(persona.scratch.name)
      .strip()
      .removeprefix("is")
      .strip()
    )
    return stripped_summary

  def __chat_func_validate(gpt_response, prompt=""):
    try:
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
  prompt_input = create_prompt_input(conversation, test_input)
  prompt = create_prompt(prompt_input)
  example_output = "Isabella is talking to Klaus about what to eat for lunch."
  special_instruction = "Do not miss any important details, including who is chatting."
  fail_safe = get_fail_safe()
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    ConversationSummary,
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

  # gpt_param = {"engine": openai_config["model"], "max_tokens": 50,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  # prompt_template = "persona/prompt_template/v2/summarize_conversation_v1.txt"
  # prompt_input = create_prompt_input(conversation, test_input)
  # prompt = generate_prompt(prompt_input, prompt_template)

  # fail_safe = get_fail_safe()
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]
