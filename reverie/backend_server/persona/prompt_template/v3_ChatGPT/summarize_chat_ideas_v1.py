import traceback
from typing import Any

from ..common import openai_config, StatementsSummary, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  date = prompt_input["date"]
  context = prompt_input["context"]
  init_persona_currently = prompt_input["init_persona_currently"]
  statements = prompt_input["statements"]
  init_persona_name = prompt_input["init_persona_name"]
  target_persona_name = prompt_input["target_persona_name"]

  prompt = f"""
Current Date: {date}

{context}

Currently: {init_persona_currently}

Statements: {statements}

Summarize the most relevant statements above that can inform {init_persona_name} in his conversation with {target_persona_name}.
"""
  return prompt


def run_gpt_prompt_agent_chat_summarize_ideas(
  persona, target_persona, statements, curr_context, test_input=None, verbose=False
):
  def create_prompt_input(
    persona, target_persona, statements, curr_context, test_input=None
  ):
    prompt_input = {
      "date": persona.scratch.get_str_curr_date_str(),
      "context": curr_context,
      "init_persona_currently": persona.scratch.currently,
      "statements": statements,
      "init_persona_name": persona.scratch.name,
      "target_persona_name": target_persona.scratch.name,
    }
    return prompt_input

  # def __func_clean_up(gpt_response: Idea_Summary, prompt=""):
  #   return gpt_response.idea_summary

  # def __func_validate(gpt_response, prompt=""):
  #   try:
  #     __func_clean_up(gpt_response, prompt)
  #     return True
  #   except:
  #     traceback.print_exc()
  #     return False

  def get_fail_safe():
    return "..."

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: StatementsSummary, prompt=""):
    return gpt_response.statements_summary

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      if not isinstance(gpt_response, StatementsSummary):
        return False
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
  prompt_input = create_prompt_input(persona, target_persona, statements, curr_context)
  prompt = create_prompt(prompt_input)
  example_output = "Jane Doe is working on a project"
  fail_safe = get_fail_safe()
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    StatementsSummary,
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

  # gpt_param = {"engine": openai_config["model"], "max_tokens": 150,
  #              "temperature": 0.5, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  # prompt_template = "persona/prompt_template/v2/summarize_chat_ideas_v1.txt"
  # prompt_input = create_prompt_input(persona, target_persona, statements, curr_context)
  # prompt = generate_prompt(prompt_input, prompt_template)

  # fail_safe = get_fail_safe()
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]
