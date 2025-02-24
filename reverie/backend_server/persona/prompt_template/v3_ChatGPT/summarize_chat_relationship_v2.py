import traceback
from pydantic import BaseModel
from typing import Any

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  statements = prompt_input["statements"]
  init_persona_name = prompt_input["init_persona_name"]
  target_persona_name = prompt_input["target_persona_name"]

  prompt = f"""
[Statements]
{statements}
[End of statements]

Based on the statements above, summarize {init_persona_name} and {target_persona_name}'s relationship. What do they feel or know about each other?
"""
  return prompt


class RelationshipSummary(BaseModel):
  summary: str


def run_gpt_prompt_agent_chat_summarize_relationship(
  persona, target_persona, statements, test_input=None, verbose=False
):
  def create_prompt_input(persona, target_persona, statements, test_input=None):
    prompt_input = {
      "statements": statements,
      "init_persona_name": persona.scratch.name,
      "target_persona_name": target_persona.scratch.name,
    }
    return prompt_input

  # def __func_clean_up(gpt_response: ChatSummarizeRelationship, prompt=""):
  #   return gpt_response.summary

  # def __func_validate(gpt_response, prompt=""):
  #   try:
  #     if not isinstance(gpt_response, ChatSummarizeRelationship):
  #       return False
  #     __func_clean_up(gpt_response, prompt)
  #     return True
  #   except:
  #     traceback.print_exc()
  #     return False

  def get_fail_safe():
    return "..."

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: RelationshipSummary, prompt=""):
    return gpt_response.summary

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      if not isinstance(gpt_response, RelationshipSummary):
        return False
      __chat_func_clean_up(gpt_response, prompt)
      return True
    except Exception:
      traceback.print_exc()
      return False

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 200,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(persona, target_persona, statements)
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe()
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    RelationshipSummary,
    "",
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

  # gpt_param = {"engine": openai_config["model"], "max_tokens": 150,
  #              "temperature": 0.5, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  # prompt_template = "persona/prompt_template/v2/summarize_chat_relationship_v1.txt"
  # prompt_input = create_prompt_input(persona, target_persona, statements)
  # prompt = generate_prompt(prompt_input, prompt_template)

  # fail_safe = get_fail_safe()
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]
