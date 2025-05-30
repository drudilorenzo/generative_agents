"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: run_gpt_prompt.py
Description: Defines all run gpt prompt functions. These functions directly
interface with the safe_generate_response function.
"""

import copy
import json
import traceback

from .common import openai_config

# Re-export LLM call functions
from .safety.anthromorphosization_v1 import run_gpt_generate_safety_score  # noqa: F401
from .v1.action_location_arena_vMar11 import run_gpt_prompt_action_arena  # noqa: F401
from .v1.action_location_sector_v1 import run_gpt_prompt_action_sector  # noqa: F401
from .v1.action_object_v2 import run_gpt_prompt_action_game_object  # noqa: F401
from .v2.daily_planning_v6 import run_gpt_prompt_daily_plan  # noqa: F401
from .v2.decide_to_react_v1 import run_gpt_prompt_decide_to_react  # noqa: F401
from .v2.decide_to_talk_v2 import run_gpt_prompt_decide_to_talk  # noqa: F401
from .v2.generate_event_triple_v1 import (
  run_gpt_prompt_event_triple,  # noqa: F401
  run_gpt_prompt_act_obj_event_triple,  # noqa: F401
)
from .v2.generate_hourly_schedule_v2 import run_gpt_prompt_generate_hourly_schedule  # noqa: F401
from .v2.generate_next_convo_line_v1 import run_gpt_prompt_generate_next_convo_line  # noqa: F401
from .v2.insight_and_evidence_v1 import run_gpt_prompt_insight_and_guidance  # noqa: F401
from .v2.new_decomp_schedule_v1 import run_gpt_prompt_new_decomp_schedule  # noqa: F401
from .v2.planning_thought_on_convo_v1 import run_gpt_prompt_planning_thought_on_convo  # noqa: F401
from .v2.prioritized_event_reaction import run_gpt_prompt_prioritized_event_reaction  # noqa: F401
from .v2.task_decomp_v3 import run_gpt_prompt_task_decomp  # noqa: F401
from .v2.wake_up_hour_v1 import run_gpt_prompt_wake_up_hour  # noqa: F401
from .v2.whisper_inner_thought_v1 import run_gpt_prompt_generate_whisper_inner_thought  # noqa: F401
from .v3_ChatGPT.generate_focal_pt_v1 import run_gpt_prompt_focal_pt  # noqa: F401
from .v3_ChatGPT.generate_obj_event_v1 import run_gpt_prompt_act_obj_desc  # noqa: F401
from .v3_ChatGPT.generate_pronunciatio_v1 import run_gpt_prompt_pronunciatio  # noqa: F401
from .v3_ChatGPT.iterative_convo_v1 import run_gpt_generate_iterative_chat_utt  # noqa: F401
from .v3_ChatGPT.memo_on_convo_v1 import run_gpt_prompt_memo_on_convo  # noqa: F401
from .v3_ChatGPT.poignancy_chat_v1 import run_gpt_prompt_chat_poignancy  # noqa: F401
from .v3_ChatGPT.poignancy_event_v1 import run_gpt_prompt_event_poignancy  # noqa: F401
from .v3_ChatGPT.summarize_chat_ideas_v1 import (
  run_gpt_prompt_agent_chat_summarize_ideas,  # noqa: F401
)
from .v3_ChatGPT.summarize_chat_relationship_v2 import (
  run_gpt_prompt_agent_chat_summarize_relationship,  # noqa: F401
)
from .v3_ChatGPT.summarize_conversation_v1 import run_gpt_prompt_summarize_conversation  # noqa: F401
from .v3_ChatGPT.summarize_ideas_v1 import run_gpt_prompt_summarize_ideas  # noqa: F401

import sys

sys.path.append("../../")
from persona.prompt_template.gpt_structure import (
  generate_prompt,
  ChatGPT_safe_generate_response,
)

# USE_REGEX = True


def extract_first_json_dict(data_str):
  # Find the first occurrence of a JSON object within the string
  start_idx = data_str.find("{")
  end_idx = data_str.find("}", start_idx) + 1

  # Check if both start and end indices were found
  if start_idx == -1 or end_idx == 0:
    return None

  # Extract the first JSON dictionary
  json_str = data_str[start_idx:end_idx]

  try:
    # Attempt to parse the JSON data
    json_dict = json.loads(json_str)
    return json_dict
  except json.JSONDecodeError:
    traceback.print_exc()
    # If parsing fails, return None
    return None


# def get_random_alphanumeric(i=6, j=6):
#   """
#   Returns a random alpha numeric strength that has the length of somewhere
#   between i and j.

#   INPUT:
#     i: min_range for the length
#     j: max_range for the length
#   OUTPUT:
#     an alpha numeric str with the length of somewhere between i and j.
#   """
#   k = random.randint(i, j)
#   x = ''.join(random.choices(string.ascii_letters + string.digits, k=k))
#   return x


##############################################################################
# CHAPTER 1: Run GPT Prompt
##############################################################################


# Takes a plugin prompt template filepath and returns an LLM response string
def run_plugin(
  plugin_template,
  current_movements,
  personas,
  verbose=False,
):
  def create_prompt_input(
    persona1,
    persona2,
    persona3,
    movements,
    test_input=None,
  ):
    if test_input:
      return test_input

    game_state = copy.deepcopy(movements)
    personas = game_state["persona"]
    for persona in personas:
      persona_state = personas[persona]
      del persona_state["chat"]
      personas[persona] = persona_state
    game_state["persona"] = personas

    conversation = list(movements["persona"].values())[0]["chat"]

    prompt_input = [
      persona1.scratch.get_str_learned(),
      persona2.scratch.get_str_learned(),
      persona3.scratch.get_str_learned(),
      game_state,
      conversation,
      persona1.scratch.get_str_firstname(),
      persona2.scratch.get_str_firstname(),
      persona3.scratch.get_str_firstname(),
    ]

    return prompt_input

  def __chat_func_clean_up(gpt_response, prompt=""):
    gpt_response = extract_first_json_dict(gpt_response)
    cleaned_dict = dict()

    for key, val in gpt_response.items():
      cleaned_dict[key] = False

      if "t" in str(val) or "T" in str(val):
        cleaned_dict[key] = True

    return cleaned_dict

  def __chat_func_validate(gpt_response, prompt=""):
    print("Validating...")

    try:
      print(extract_first_json_dict(gpt_response))
      return True
    except:
      traceback.print_exc()
      return False

  def get_fail_safe():
    cleaned_dict = {"error": "error"}
    return cleaned_dict

  persona_list = list(personas.values())

  prompt_input = create_prompt_input(
    persona1=persona_list[0],
    persona2=persona_list[1],
    persona3=persona_list[2],
    movements=current_movements,
  )
  prompt = generate_prompt(prompt_input, plugin_template)
  print(prompt)
  fail_safe = get_fail_safe()
  raw_output, output = ChatGPT_safe_generate_response(
    prompt,
    repeat=3,
    fail_safe_response=fail_safe,
    func_validate=__chat_func_validate,
    func_clean_up=__chat_func_clean_up,
    verbose=verbose,
  )
  print(output)

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

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


# def run_gpt_prompt_create_conversation(persona, target_persona, curr_loc,
#                                        test_input=None, verbose=False):
#   def create_prompt_input(init_persona, target_persona, curr_loc,
#                           test_input=None):

#     prev_convo_insert = "\n"
#     if init_persona.a_mem.seq_chat:
#       for i in init_persona.a_mem.seq_chat:
#         if i.object == target_persona.scratch.name:
#           v1 = int((init_persona.scratch.curr_time - i.created).total_seconds()/60)
#           prev_convo_insert += f'{str(v1)} minutes ago, they had the following conversation.\n'
#           for row in i.filling:
#             prev_convo_insert += f'{row[0]}: "{row[1]}"\n'
#           break
#     if prev_convo_insert == "\n":
#       prev_convo_insert = ""
#     if init_persona.a_mem.seq_chat:
#       if int((init_persona.scratch.curr_time - init_persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480:
#         prev_convo_insert = ""

#     init_persona_thought_nodes = init_persona.a_mem.retrieve_relevant_thoughts(target_persona.scratch.act_event[0],
#                                 target_persona.scratch.act_event[1],
#                                 target_persona.scratch.act_event[2])
#     init_persona_thought = ""
#     for i in init_persona_thought_nodes:
#       init_persona_thought += f"-- {i.description}\n"

#     target_persona_thought_nodes = target_persona.a_mem.retrieve_relevant_thoughts(init_persona.scratch.act_event[0],
#                                 init_persona.scratch.act_event[1],
#                                 init_persona.scratch.act_event[2])
#     target_persona_thought = ""
#     for i in target_persona_thought_nodes:
#       target_persona_thought += f"-- {i.description}\n"

#     init_persona_curr_desc = ""
#     if init_persona.scratch.planned_path:
#       init_persona_curr_desc = f"{init_persona.name} is on the way to {init_persona.scratch.act_description}"
#     else:
#       init_persona_curr_desc = f"{init_persona.name} is {init_persona.scratch.act_description}"

#     target_persona_curr_desc = ""
#     if target_persona.scratch.planned_path:
#       target_persona_curr_desc = f"{target_persona.name} is on the way to {target_persona.scratch.act_description}"
#     else:
#       target_persona_curr_desc = f"{target_persona.name} is {target_persona.scratch.act_description}"

#     curr_loc = curr_loc["arena"]

#     prompt_input = []
#     prompt_input += [init_persona.scratch.get_str_iss()]
#     prompt_input += [target_persona.scratch.get_str_iss()]

#     prompt_input += [init_persona.name]
#     prompt_input += [target_persona.name]
#     prompt_input += [init_persona_thought]

#     prompt_input += [target_persona.name]
#     prompt_input += [init_persona.name]
#     prompt_input += [target_persona_thought]

#     prompt_input += [init_persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S")]

#     prompt_input += [init_persona_curr_desc]
#     prompt_input += [target_persona_curr_desc]

#     prompt_input += [prev_convo_insert]

#     prompt_input += [init_persona.name]
#     prompt_input += [target_persona.name]

#     prompt_input += [curr_loc]
#     prompt_input += [init_persona.name]
#     return prompt_input

#   def __func_clean_up(gpt_response, prompt=""):
#     # print ("???")
#     # print (gpt_response)

#     gpt_response = (prompt + gpt_response).split("What would they talk about now?")[-1].strip()
#     content = re.findall('"([^"]*)"', gpt_response)

#     speaker_order = []
#     for i in gpt_response.split("\n"):
#       name = i.split(":")[0].strip()
#       if name:
#         speaker_order += [name]

#     ret = []
#     for count, speaker in enumerate(speaker_order):
#       ret += [[speaker, content[count]]]

#     return ret

#   def __func_validate(gpt_response, prompt=""):
#     try:
#       __func_clean_up(gpt_response, prompt)
#       return True
#     except:
#       traceback.print_exc()
#       return False

#   def get_fail_safe(init_persona, target_persona):
#     convo = [[init_persona.name, "Hi!"],
#              [target_persona.name, "Hi!"]]
#     return convo


#   gpt_param = {"engine": openai_config["model"], "max_tokens": 1000,
#                "temperature": 0.7, "top_p": 1, "stream": False,
#                "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   prompt_template = "persona/prompt_template/v2/create_conversation_v2.txt"
#   prompt_input = create_prompt_input(persona, target_persona, curr_loc,
#                                      test_input)
#   prompt = generate_prompt(prompt_input, prompt_template)

#   fail_safe = get_fail_safe(persona, target_persona)
#   output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
#                                    __func_validate, __func_clean_up)

#   if debug or verbose:
#     print_run_prompts(prompt_template, persona, gpt_param,
#                       prompt_input, prompt, output)

#   return output, [output, prompt, gpt_param, prompt_input, fail_safe]


# class Keywords(BaseModel):
#   emotive_keywords: list[str]
#   factual_keywords: list[str]
#   all_keywords: list[list]

# def run_gpt_prompt_extract_keywords(persona, description, test_input=None, verbose=False):
#   def create_prompt_input(description, test_input=None):
#     if "\n" in description:
#       description = description.replace("\n", " <LINE_BREAK> ")
#     prompt_input = [description]
#     return prompt_input

#   def __func_clean_up(gpt_response, prompt=""):
#     print ("???")
#     print (gpt_response)
#     gpt_response = gpt_response.strip().split("Emotive keywords:")
#     factual = [i.strip() for i in gpt_response[0].split(",")]
#     emotive = [i.strip() for i in gpt_response[1].split(",")]
#     all_keywords = factual + emotive
#     ret = []
#     for i in all_keywords:
#       if i:
#         i = i.lower()
#         if i[-1] == ".":
#           i = i[:-1]
#         ret += [i]
#     print (ret)
#     return set(ret)

#   def __func_validate(gpt_response, prompt=""):
#     try:
#       __func_clean_up(gpt_response, prompt)
#       return True
#     except:
#       traceback.print_exc()
#       return False

#   def get_fail_safe():
#     return []

#   gpt_param = {"engine": openai_config["model"], "max_tokens": 50,
#                "temperature": 0, "top_p": 1, "stream": False,
#                "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   prompt_template = "persona/prompt_template/v2/get_keywords_v1.txt"
#   prompt_input = create_prompt_input(description, test_input)
#   prompt = generate_prompt(prompt_input, prompt_template)

#   fail_safe = get_fail_safe()
#   output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
#                                    __func_validate, __func_clean_up)

#   if debug or verbose:
#     print_run_prompts(prompt_template, persona, gpt_param,
#                       prompt_input, prompt, output)

#   return output, [output, prompt, gpt_param, prompt_input, fail_safe]


# def run_gpt_prompt_keyword_to_thoughts(persona, keyword, concept_summary, test_input=None, verbose=False):
#   def create_prompt_input(persona, keyword, concept_summary, test_input=None):
#     prompt_input = [keyword, concept_summary, persona.name]
#     return prompt_input

#   def __func_clean_up(gpt_response, prompt=""):
#     gpt_response = gpt_response.strip()
#     return gpt_response

#   def __func_validate(gpt_response, prompt=""):
#     try:
#       __func_clean_up(gpt_response, prompt)
#       return True
#     except:
#       traceback.print_exc()
#       return False

#   def get_fail_safe():
#     return ""

#   gpt_param = {"engine": openai_config["model"], "max_tokens": 40,
#                "temperature": 0.7, "top_p": 1, "stream": False,
#                "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   prompt_template = "persona/prompt_template/v2/keyword_to_thoughts_v1.txt"
#   prompt_input = create_prompt_input(persona, keyword, concept_summary)
#   prompt = generate_prompt(prompt_input, prompt_template)

#   fail_safe = get_fail_safe()
#   output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
#                                    __func_validate, __func_clean_up)

#   if debug or verbose:
#     print_run_prompts(prompt_template, persona, gpt_param,
#                       prompt_input, prompt, output)

#   return output, [output, prompt, gpt_param, prompt_input, fail_safe]


# def run_gpt_prompt_convo_to_thoughts(persona,
#                                     init_persona_name,
#                                     target_persona_name,
#                                     convo_str,
#                                     fin_target, test_input=None, verbose=False):
#   def create_prompt_input(init_persona_name,
#                                     target_persona_name,
#                                     convo_str,
#                                     fin_target, test_input=None):
#     prompt_input = [init_persona_name,
#                     target_persona_name,
#                     convo_str,
#                     init_persona_name,
#                     fin_target]
#     return prompt_input

#   def __func_clean_up(gpt_response, prompt=""):
#     gpt_response = gpt_response.strip()
#     return gpt_response

#   def __func_validate(gpt_response, prompt=""):
#     try:
#       __func_clean_up(gpt_response, prompt)
#       return True
#     except:
#       traceback.print_exc()
#       return False

#   def get_fail_safe():
#     return ""

#   gpt_param = {"engine": openai_config["model"], "max_tokens": 40,
#                "temperature": 0.7, "top_p": 1, "stream": False,
#                "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   prompt_template = "persona/prompt_template/v2/convo_to_thoughts_v1.txt"
#   prompt_input = create_prompt_input(init_persona_name,
#                                     target_persona_name,
#                                     convo_str,
#                                     fin_target)
#   prompt = generate_prompt(prompt_input, prompt_template)

#   fail_safe = get_fail_safe()
#   output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
#                                    __func_validate, __func_clean_up)

#   if debug or verbose:
#     print_run_prompts(prompt_template, persona, gpt_param,
#                       prompt_input, prompt, output)

#   return output, [output, prompt, gpt_param, prompt_input, fail_safe]


# def run_gpt_prompt_thought_poignancy(persona, event_description, test_input=None, verbose=False):
#   def create_prompt_input(persona, event_description, test_input=None):
#     prompt_input = [persona.scratch.name,
#                     persona.scratch.get_str_iss(),
#                     persona.scratch.name,
#                     event_description]
#     return prompt_input

#   def __func_clean_up(gpt_response, prompt=""):
#     gpt_response = int(gpt_response.strip())
#     return gpt_response

#   def __func_validate(gpt_response, prompt=""):
#     try:
#       __func_clean_up(gpt_response, prompt)
#       return True
#     except:
#       traceback.print_exc()
#       return False

#   def get_fail_safe():
#     return 4

#   # ChatGPT Plugin ===========================================================
#   def __chat_func_clean_up(gpt_response, prompt=""): ############
#     gpt_response = int(gpt_response)
#     return gpt_response

#   def __chat_func_validate(gpt_response, prompt=""): ############
#     try:
#       __func_clean_up(gpt_response, prompt)
#       return True
#     except:
#       traceback.print_exc()
#       return False

#   print ("DEBUG 8") ########
#   gpt_param = {"engine": openai_config["model"], "max_tokens": 15,
#                "temperature": 0, "top_p": 1, "stream": False,
#                "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   prompt_template = "persona/prompt_template/v3_ChatGPT/poignancy_thought_v1.txt" ########
#   prompt_input = create_prompt_input(persona, event_description)  ########
#   prompt = generate_prompt(prompt_input, prompt_template)
#   example_output = "5" ########
#   special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10." ########
#   fail_safe = get_fail_safe() ########
#   output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 3, fail_safe,
#                                           __chat_func_validate, __chat_func_clean_up, True)
#   if output != False:
#     return output, [output, prompt, gpt_param, prompt_input, fail_safe]
#   # ChatGPT Plugin ===========================================================

#   # gpt_param = {"engine": openai_config["model"], "max_tokens": 3,
#   #              "temperature": 0, "top_p": 1, "stream": False,
#   #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   # prompt_template = "persona/prompt_template/v2/poignancy_thought_v1.txt"
#   # prompt_input = create_prompt_input(persona, event_description)
#   # prompt = generate_prompt(prompt_input, prompt_template)

#   # fail_safe = get_fail_safe()
#   # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
#   #                                  __func_validate, __func_clean_up)

#   # if debug or verbose:
#   #   print_run_prompts(prompt_template, persona, gpt_param,
#   #                     prompt_input, prompt, output)

#   # return output, [output, prompt, gpt_param, prompt_input, fail_safe]


# class PromptAgentChat(BaseModel):
#   convo: list[list[str]]

# def run_gpt_prompt_agent_chat(maze, persona, target_persona,
#                                curr_context,
#                                init_summ_idea,
#                                target_summ_idea, test_input=None, verbose=False):
#   def create_prompt_input(persona, target_persona, curr_context, init_summ_idea, target_summ_idea, test_input=None):
#     prev_convo_insert = "\n"
#     if persona.a_mem.seq_chat:
#       for i in persona.a_mem.seq_chat:
#         if i.object == target_persona.scratch.name:
#           v1 = int((persona.scratch.curr_time - i.created).total_seconds()/60)
#           prev_convo_insert += f'{str(v1)} minutes ago, {persona.scratch.name} and {target_persona.scratch.name} were already {i.description} This context takes place after that conversation.'
#           break
#     if prev_convo_insert == "\n":
#       prev_convo_insert = ""
#     if persona.a_mem.seq_chat:
#       if int((persona.scratch.curr_time - persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480:
#         prev_convo_insert = ""
#     print (prev_convo_insert)

#     curr_sector = f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"
#     curr_arena= f"{maze.access_tile(persona.scratch.curr_tile)['arena']}"
#     curr_location = f"{curr_arena} in {curr_sector}"

#     prompt_input = [persona.scratch.currently,
#                     target_persona.scratch.currently,
#                     prev_convo_insert,
#                     curr_context,
#                     curr_location,

#                     persona.scratch.name,
#                     init_summ_idea,
#                     persona.scratch.name,
#                     target_persona.scratch.name,

#                     target_persona.scratch.name,
#                     target_summ_idea,
#                     target_persona.scratch.name,
#                     persona.scratch.name,

#                     persona.scratch.name]
#     return prompt_input

#   def __func_clean_up(gpt_response: PromptAgentChat, prompt=""):
#     print (gpt_response)

#     gpt_response = (prompt + gpt_response).split("Here is their conversation.")[-1].strip()
#     content = re.findall('"([^"]*)"', gpt_response)

#     speaker_order = []
#     for i in gpt_response.split("\n"):
#       name = i.split(":")[0].strip()
#       if name:
#         speaker_order += [name]

#     ret = []
#     for count, speaker in enumerate(speaker_order):
#       ret += [[speaker, content[count]]]

#     return ret

#   def __func_validate(gpt_response, prompt=""):
#     try:
#       __func_clean_up(gpt_response, prompt)
#       return True
#     except:
#       traceback.print_exc()
#       return False

#   def get_fail_safe():
#     return "..."

#   # ChatGPT Plugin ===========================================================
#   def __chat_func_clean_up(gpt_response, prompt=""): ############
#     # ret = ast.literal_eval(gpt_response)

#     print ("DEBUG HERE (run_gpt_prompt_agent_chat)")
#     for row in gpt_response:
#       print (row)

#     return gpt_response

#   def __chat_func_validate(gpt_response, prompt=""): ############
#     return True

#   gpt_param = {"engine": openai_config["model"], "max_tokens": 15,
#                "temperature": 0, "top_p": 1, "stream": False,
#                "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   prompt_template = "persona/prompt_template/v3_ChatGPT/agent_chat_v1.txt" ########
#   prompt_input = create_prompt_input(persona, target_persona, curr_context, init_summ_idea, target_summ_idea)  ########
#   prompt = generate_prompt(prompt_input, prompt_template)
#   example_output = '[["Jane Doe", "Hi!"], ["John Doe", "Hello there!"] ... ]' ########
#   special_instruction = 'The output should be a list of list where the inner lists are in the form of ["<Name>", "<Utterance>"].' ########
#   fail_safe = get_fail_safe() ########
#   output = generate_structured_response(
#     prompt,
#     gpt_param,
#     PromptAgentChat,
#     3,
#     fail_safe,
#     __func_validate,
#     __func_clean_up
#     )

#   if output != False:
#     return output, [output, prompt, gpt_param, prompt_input, fail_safe]
#   # ChatGPT Plugin ===========================================================

#   # gpt_param = {"engine": openai_config["model"], "max_tokens": 2000,
#   #              "temperature": 0.7, "top_p": 1, "stream": False,
#   #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
#   # prompt_template = "persona/prompt_template/v2/agent_chat_v1.txt"
#   # prompt_input = create_prompt_input(persona, target_persona, curr_context, init_summ_idea, target_summ_idea)
#   # prompt = generate_prompt(prompt_input, prompt_template)

#   # fail_safe = get_fail_safe()
#   # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
#   #                                  __func_validate, __func_clean_up)

#   # if debug or verbose:
#   #   print_run_prompts(prompt_template, persona, gpt_param,
#   #                     prompt_input, prompt, output)

#   # return output, [output, prompt, gpt_param, prompt_input, fail_safe]

# # =======================
# # =======================
# # =======================
# # =======================
