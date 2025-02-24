from pydantic import BaseModel
import traceback
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  persona_name = prompt_input["persona_name"]
  identity_stable_set = prompt_input["identity_stable_set"]
  interlocutor_description = prompt_input["interlocutor_description"]
  conversation = prompt_input["conversation"]
  persona_knowledge = prompt_input["persona_knowledge"]

  prompt = f"""
Here is some basic information about {persona_name}.
{identity_stable_set}

===
Following is a conversation between {persona_name} and {interlocutor_description}.

{conversation}

(Note -- This is the only information that {persona_name} has: {persona_knowledge})

Next line:
{persona_name}:
"""
  return prompt


class NextConversationLine(BaseModel):
  next_conversation_line: str


def run_gpt_prompt_generate_next_convo_line(
  persona,
  interlocutor_desc,
  prev_convo,
  retrieved_summary,
  test_input=None,
  verbose=False,
):
  def create_prompt_input(
    persona, interlocutor_desc, prev_convo, retrieved_summary, test_input=None
  ):
    prompt_input = {
      "persona_name": persona.scratch.name,
      "identity_stable_set": persona.scratch.get_str_iss(),
      "interlocutor_description": interlocutor_desc,
      "conversation": prev_convo,
      "persona_knowledge": retrieved_summary,
    }
    return prompt_input

  def __func_clean_up(gpt_response: NextConversationLine, prompt=""):
    return gpt_response.next_conversation_line.strip().strip('"')

  def __func_validate(gpt_response, prompt=""):
    try:
      if not isinstance(gpt_response, NextConversationLine):
        return False
      __func_clean_up(gpt_response, prompt)
      return True
    except Exception:
      traceback.print_exc()
      return False

  def get_fail_safe():
    return "..."

  # # ChatGPT Plugin ===========================================================
  # def __chat_func_clean_up(gpt_response, prompt=""): ############
  #   return gpt_response.split('"')[0].strip()

  # def __chat_func_validate(gpt_response, prompt=""): ############
  #   try:
  #     __func_clean_up(gpt_response, prompt)
  #     return True
  #   except:
  #     return False

  # print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 15") ########
  # gpt_param = {"engine": openai_config["model"], "max_tokens": 15,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  # prompt_template = "persona/prompt_template/v3_ChatGPT/generate_next_convo_line_v1.txt" ########
  # prompt_input = create_prompt_input(persona, interlocutor_desc, prev_convo, retrieved_summary)  ########
  # prompt = generate_prompt(prompt_input, prompt_template)
  # example_output = 'Hello' ########
  # special_instruction = 'The output should be a string that responds to the question. Again, only use the context included in the "Note" to generate the response' ########
  # fail_safe = get_fail_safe() ########
  # output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 3, fail_safe,
  #                                         __chat_func_validate, __chat_func_clean_up, True)
  # if output != False:
  #   return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # # ChatGPT Plugin ===========================================================

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 500,
    "temperature": 1,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(
    persona, interlocutor_desc, prev_convo, retrieved_summary
  )
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt,
    gpt_param,
    NextConversationLine,
    5,
    fail_safe,
    __func_validate,
    __func_clean_up,
  )
  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
