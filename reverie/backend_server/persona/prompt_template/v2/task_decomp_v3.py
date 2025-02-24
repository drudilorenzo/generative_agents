from pydantic import BaseModel
import traceback
import datetime
from typing import Any

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  identity_stable_set = prompt_input["identity_stable_set"]
  broad_schedule_summary = prompt_input["broad_schedule_summary"]
  persona_firstname = prompt_input["persona_firstname"]
  action = prompt_input["action"]
  action_duration = prompt_input["action_duration"]
  action_time_range = prompt_input["action_time_range"]

  prompt = f"""
Describe subtasks in 5 min increments.

--- Example ---
Name: Kelly Bronson
Age: 35
Backstory: Kelly always wanted to be a teacher, and now she teaches kindergarten. During the week, she dedicates herself to her students, but on the weekends, she likes to try out new restaurants and hang out with friends. She is very warm and friendly, and loves caring for others.
Personality: sweet, gentle, meticulous
Location: Kelly is in an older condo that has the following areas: [kitchen, bedroom, dining, porch, office, bathroom, living room, hallway].
Currently: Kelly is a teacher during the school year. She teaches at the school but works on lesson plans at home. She is currently living alone in a single bedroom condo.
Daily plan requirement: Kelly is planning to teach during the morning and work from home in the afternoon.

Today is Saturday May 10. From 08:00am ~09:00am, Kelly is planning on having breakfast, from 09:00am ~ 12:00pm, Kelly is planning on working on the next day's kindergarten lesson plan, and from 12:00 ~ 13pm, Kelly is planning on taking a break.
In 5 min increments, list the subtasks Kelly does when Kelly is working on the next day's kindergarten lesson plan from 09:00am ~ 12:00pm (total duration in minutes: 180):
1) Kelly is reviewing the kindergarten curriculum standards. (duration in minutes: 15, minutes left: 165)
2) Kelly is brainstorming ideas for the lesson. (duration in minutes: 30, minutes left: 135)
3) Kelly is creating the lesson plan. (duration in minutes: 30, minutes left: 105)
4) Kelly is creating materials for the lesson. (duration in minutes: 30, minutes left: 75)
5) Kelly is taking a break. (duration in minutes: 15, minutes left: 60)
6) Kelly is reviewing the lesson plan. (duration in minutes: 30, minutes left: 30)
7) Kelly is making final changes to the lesson plan. (duration in minutes: 15, minutes left: 15)
8) Kelly is printing the lesson plan. (duration in minutes: 10, minutes left: 5)
9) Kelly is putting the lesson plan in her bag. (duration in minutes: 5, minutes left: 0)
---
{identity_stable_set}
{broad_schedule_summary}
In 5 min increments, list the subtasks {persona_firstname} does when {persona_firstname} is {action} from {action_time_range} (total duration in minutes: {action_duration}). Use present progressive tense (e.g., "printing the lesson plan").
"""
  return prompt


class Subtask(BaseModel):
  task: str
  duration: int
  minutes_left: int


class TaskDecomposition(BaseModel):
  subtasks: list[Subtask]


def run_gpt_prompt_task_decomp(persona, task, duration, test_input=None, verbose=False):
  def create_prompt_input(persona, task, duration, test_input=None, debug=False):
    """
    Today is Saturday June 25. From 00:00 ~ 06:00am, Maeve is
    planning on sleeping, 06:00 ~ 07:00am, Maeve is
    planning on waking up and doing her morning routine,
    and from 07:00am ~08:00am, Maeve is planning on having breakfast.
    """
    curr_f_org_index = persona.scratch.get_f_daily_schedule_hourly_org_index()
    all_indices = []
    # if curr_f_org_index > 0:
    #   all_indices += [curr_f_org_index-1]
    all_indices += [curr_f_org_index]
    if curr_f_org_index + 1 <= len(persona.scratch.f_daily_schedule_hourly_org):
      all_indices += [curr_f_org_index + 1]
    if curr_f_org_index + 2 <= len(persona.scratch.f_daily_schedule_hourly_org):
      all_indices += [curr_f_org_index + 2]

    curr_time_range = ""

    if debug:
      print("DEBUG")
      print(persona.scratch.f_daily_schedule_hourly_org)
      print(all_indices)

    summary_str = f"Today is {persona.scratch.curr_time.strftime('%B %d, %Y')}. "
    summary_str += "From "
    for index in all_indices:
      if debug:
        print("index", index)

      if index < len(persona.scratch.f_daily_schedule_hourly_org):
        start_min = 0
        for i in range(index):
          start_min += persona.scratch.f_daily_schedule_hourly_org[i][1]
        end_min = start_min + persona.scratch.f_daily_schedule_hourly_org[index][1]
        start_time = datetime.datetime.strptime(
          "00:00:00", "%H:%M:%S"
        ) + datetime.timedelta(minutes=start_min)
        end_time = datetime.datetime.strptime(
          "00:00:00", "%H:%M:%S"
        ) + datetime.timedelta(minutes=end_min)
        start_time_str = start_time.strftime("%H:%M%p")
        end_time_str = end_time.strftime("%H:%M%p")
        summary_str += f"{start_time_str} ~ {end_time_str}, {persona.name} is planning on {persona.scratch.f_daily_schedule_hourly_org[index][0]}, "
        if curr_f_org_index + 1 == index:
          curr_time_range = f"{start_time_str} ~ {end_time_str}"
    summary_str = summary_str[:-2] + "."

    prompt_input = {
      "identity_stable_set": persona.scratch.get_str_iss(),
      "broad_schedule_summary": summary_str,
      "persona_firstname": persona.scratch.get_str_firstname(),
      "action": task,
      "action_duration": duration,
      "action_time_range": curr_time_range,
    }
    return prompt_input

  def __func_clean_up(
    gpt_response: TaskDecomposition, prompt="", debug=False
  ) -> list[list]:
    if debug:
      print(gpt_response)
      print("-==- -==- -==- ")
      print("(cleanup func): Enter function")

    final_task_list = []

    for count, subtask in enumerate(gpt_response.subtasks):
      task = subtask.task.strip().strip(".")

      # Get rid of "1)", "2)", etc. at start of string if it exists
      if task[1] == ")":
        task = task[2:].strip()
      # Get rid of "Isabella is " at start of string if it exists
      task = task.removeprefix(persona.scratch.get_str_firstname()).strip()
      task = task.removeprefix("is").strip()

      final_task_list += [[task, subtask.duration]]

    if debug:
      print("(cleanup func) Unpacked (final_task_list)): ", final_task_list)
      print("(cleanup func) Prompt:", prompt)

    total_expected_min = int(duration)

    if debug:
      print("(cleanup func) Expected Minutes:", total_expected_min)

    # TODO -- now, you need to make sure that this is the same as the sum of
    #         the current action sequence.
    curr_min_slot = [
      ["dummy", -1],
    ]  # (task_name, task_index)
    for count, split_task in enumerate(final_task_list):
      i_task = split_task[0]
      i_duration = split_task[1]

      i_duration -= i_duration % 5
      if i_duration > 0:
        for _j in range(i_duration):
          curr_min_slot += [[i_task, count]]
    curr_min_slot = curr_min_slot[1:]

    if len(curr_min_slot) > total_expected_min:
      last_task = curr_min_slot[60]
      for i in range(1, 6):
        curr_min_slot[-1 * i] = last_task
    elif len(curr_min_slot) < total_expected_min:
      last_task = curr_min_slot[-1]
      for i in range(total_expected_min - len(curr_min_slot)):
        curr_min_slot += [last_task]

    return_task_list = [
      ["dummy", -1],
    ]
    for task, _task_index in curr_min_slot:
      if task != return_task_list[-1][0]:
        return_task_list += [[task, 1]]
      else:
        return_task_list[-1][1] += 1
    final_task_list = return_task_list[1:]

    return final_task_list

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt)
    except Exception as e:
      print("Validation failed: ", e)
      traceback.print_exc()
      return False
    return gpt_response

  def get_fail_safe():
    fs = [["idle", 5]]
    return fs

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 5000,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(persona, task, duration)
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe()

  output = safe_generate_structured_response(
    prompt,
    gpt_param,
    TaskDecomposition,
    5,
    fail_safe,
    __func_validate,
    __func_clean_up,
  )

  if verbose:
    print("DEBUG")
    print("PROMPT:")
    print(prompt)
    print("\nOUTPUT:")
    print(output)

  fin_output = []
  time_sum = 0
  for i_task, i_duration in output:
    time_sum += int(i_duration)

    # if time_sum < duration:
    if time_sum <= duration:
      fin_output += [[i_task, i_duration]]
    else:
      break

  ftime_sum = 0
  for _fi_task, fi_duration in fin_output:
    ftime_sum += fi_duration

  fin_output[-1][1] += duration - ftime_sum
  output = fin_output

  task_decomp = output
  ret = []
  for decomp_task, duration in task_decomp:
    ret += [[f"{task} ({decomp_task})", duration]]
  output = ret

  if verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
