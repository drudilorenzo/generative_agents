import traceback
from pydantic import BaseModel
from typing import Any

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import ChatGPT_safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  identity_stable_set = prompt_input["identity_stable_set"]
  init_persona_name = prompt_input["init_persona_name"]
  retrieved_memories = prompt_input["retrieved_memories"]
  prev_conversation = prompt_input["prev_conversation"]
  curr_location = prompt_input["curr_location"]
  curr_situation = prompt_input["curr_situation"]
  target_persona_name = prompt_input["target_persona_name"]
  curr_conversation = prompt_input["curr_conversation"]

  prompt = f"""
Context for the task:

PART 1.
{identity_stable_set}

Here are the memories in {init_persona_name}'s mind:
{retrieved_memories}

PART 2.
Past Context:
{prev_conversation}

Current Location: {curr_location}

Current Context:
{curr_situation}

{init_persona_name} and {target_persona_name} are chatting. Here is their conversation so far:
{curr_conversation}

---
Task: Given the above, what should {init_persona_name} say to {target_persona_name} next in the conversation? And will it end the conversation?
"""
  return prompt


class ChatUtterance(BaseModel):
  utterance: str
  did_conversation_end: bool


def run_gpt_generate_iterative_chat_utt(
  maze,
  init_persona,
  target_persona,
  retrieved,
  curr_context,
  curr_chat,
  test_input=None,
  verbose=False,
):
  def create_prompt_input(
    maze,
    init_persona,
    target_persona,
    retrieved,
    curr_context,
    curr_chat,
    test_input=None,
  ):
    persona = init_persona
    prev_convo_insert = "\n"
    if persona.a_mem.seq_chat:
      for i in persona.a_mem.seq_chat:
        if i.object == target_persona.scratch.name:
          v1 = int((persona.scratch.curr_time - i.created).total_seconds() / 60)
          prev_convo_insert += f"{str(v1)} minutes ago, {persona.scratch.name} and {target_persona.scratch.name} were already {i.description} This context takes place after that conversation."
          break
    if prev_convo_insert == "\n":
      prev_convo_insert = ""
    if persona.a_mem.seq_chat:
      if (
        int(
          (
            persona.scratch.curr_time - persona.a_mem.seq_chat[-1].created
          ).total_seconds()
          / 60
        )
        > 480
      ):
        prev_convo_insert = ""
    print(prev_convo_insert)

    curr_sector = f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"
    curr_arena = f"{maze.access_tile(persona.scratch.curr_tile)['arena']}"
    curr_location = f"{curr_arena} in {curr_sector}"

    retrieved_str = ""
    for key, vals in retrieved.items():
      for v in vals:
        retrieved_str += f"- {v.description}\n"

    convo_str = ""
    for i in curr_chat:
      convo_str += ": ".join(i) + "\n"
    if convo_str == "":
      convo_str = "[The conversation has not started yet -- start it!]"

    init_iss = f"Here is a brief description of {init_persona.scratch.name}.\n{init_persona.scratch.get_str_iss()}"

    prompt_input = {
      "identity_stable_set": init_iss,
      "init_persona_name": init_persona.scratch.name,
      "retrieved_memories": retrieved_str,
      "prev_conversation": prev_convo_insert,
      "curr_location": curr_location,
      "curr_situation": curr_context,
      "target_persona_name": target_persona.scratch.name,
      "curr_conversation": convo_str,
    }
    return prompt_input

  def __chat_func_clean_up(gpt_response: ChatUtterance, prompt=""):
    cleaned_dict = {
      "utterance": gpt_response.utterance,
      "end": gpt_response.did_conversation_end,
    }
    return cleaned_dict

  def __chat_func_validate(gpt_response, prompt=""):
    try:
      if not isinstance(gpt_response, ChatUtterance):
        return False
      return True
    except Exception:
      traceback.print_exc()
      return False

  def get_fail_safe():
    cleaned_dict = {
      "utterance": "...",
      "end": False,
    }
    return cleaned_dict

  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(
    maze, init_persona, target_persona, retrieved, curr_context, curr_chat
  )
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe()
  output = ChatGPT_safe_generate_structured_response(
    prompt,
    ChatUtterance,
    repeat=3,
    fail_safe_response=fail_safe,
    func_validate=__chat_func_validate,
    func_clean_up=__chat_func_clean_up,
    verbose=verbose,
  )

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 4096,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }

  if verbose:
    print_run_prompts(
      prompt_file, init_persona, gpt_param, prompt_input, prompt, output
    )

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
