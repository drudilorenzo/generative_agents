import traceback
from typing import Any

from ..common import openai_config, StatementsSummary, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  statements = prompt_input["statements"]
  persona_name = prompt_input["persona_name"]
  question = prompt_input["question"]

  prompt = f"""
[Statements]
{statements}
[End of statements]

An interviewer said to {persona_name}:
"{question}"

Summarize the statements above that are most relevant to the interviewer's line.
"""
  return prompt


def run_gpt_prompt_summarize_ideas(
  persona, statements, question, test_input=None, verbose=False
):
  def create_prompt_input(persona, statements, question, test_input=None):
    prompt_input = {
      "statements": statements,
      "persona_name": persona.scratch.name,
      "question": question,
    }
    return prompt_input

  # def __func_clean_up(gpt_response: Idea_Summary, prompt=""):
  #   return gpt_response.idea_summary.strip()

  # def __func_validate(gpt_response, prompt=""):
  #   try:
  #     gpt_response = __func_clean_up(gpt_response, prompt)
  #     if gpt_response is None:
  #       return False
  #   except:
  #     traceback.print_exc()
  #     return False
  #   return True

  def get_fail_safe():
    return "..."

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response: StatementsSummary, prompt=""):
    return gpt_response.statements_summary.strip()

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      response = __chat_func_clean_up(gpt_response, prompt)
      if response is None or response == "":
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
  prompt_input = create_prompt_input(persona, statements, question)
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
  # prompt_template = "persona/prompt_template/v2/summarize_ideas_v1.txt"
  # prompt_input = create_prompt_input(persona, statements, question)
  # prompt = generate_prompt(prompt_input, prompt_template)

  # fail_safe = get_fail_safe()
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]
