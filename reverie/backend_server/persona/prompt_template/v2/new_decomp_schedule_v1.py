import datetime
from pydantic import BaseModel
import traceback
from typing import Any

from utils import debug
from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  persona_name = prompt_input["persona_name"]
  start_hour = prompt_input["start_hour"]
  end_hour = prompt_input["end_hour"]
  original_plan = prompt_input["original_plan"]
  new_action = prompt_input["new_action"]
  new_action_duration = prompt_input["new_action_duration"]
  new_schedule_start = prompt_input["new_schedule_start"]

  prompt = f"""
Activity format:
start_time ~ end_time -- main_task (subtask)

Here was {persona_name}'s originally planned schedule from {start_hour} to {end_hour}:
{original_plan}

But {persona_name} unexpectedly ended up {new_action} for {new_action_duration} minutes. Revise {persona_name}'s schedule from {start_hour} to {end_hour} accordingly (it has to end by {end_hour}). Use present progressive tense (e.g., "working on the lesson plan").

Revised schedule:
{new_schedule_start}
"""
  return prompt


class NewActivity(BaseModel):
  start_time: str
  end_time: str
  main_task: str
  subtask: str


class NewSchedule(BaseModel):
  schedule: list[NewActivity]


def run_gpt_prompt_new_decomp_schedule(
  persona,
  main_act_dur,
  truncated_act_dur,
  start_time_hour,
  end_time_hour,
  inserted_act,
  inserted_act_dur,
  test_input=None,
  verbose=False,
):
  def create_prompt_input(
    persona,
    main_act_dur,
    truncated_act_dur,
    start_time_hour,
    end_time_hour,
    inserted_act,
    inserted_act_dur,
    test_input=None,
  ):
    persona_name = persona.name
    start_hour_str = start_time_hour.strftime("%H:%M %p")
    end_hour_str = end_time_hour.strftime("%H:%M %p")

    original_plan = ""
    for_time = start_time_hour
    for i in main_act_dur:
      original_plan += (
        f"{for_time.strftime('%H:%M')} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime('%H:%M')} -- "
        + i[0]
      )
      original_plan += "\n"
      for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init = ""
    for_time = start_time_hour
    for count, i in enumerate(truncated_act_dur):
      new_plan_init += (
        f"{for_time.strftime('%H:%M')} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime('%H:%M')} -- "
        + i[0]
      )
      new_plan_init += "\n"
      if count < len(truncated_act_dur) - 1:
        for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init += (for_time + datetime.timedelta(minutes=int(i[1]))).strftime(
      "%H:%M"
    ) + " ~"

    prompt_input = {
      "persona_name": persona_name,
      "start_hour": start_hour_str,
      "end_hour": end_hour_str,
      "original_plan": original_plan,
      "new_action": inserted_act,
      "new_action_duration": inserted_act_dur,
      "new_schedule_start": new_plan_init,
    }
    return prompt_input

  def __func_clean_up(gpt_response: NewSchedule, prompt=""):
    new_schedule = []

    for activity in gpt_response.schedule:
      start_time = activity.start_time
      end_time = activity.end_time
      delta = datetime.datetime.strptime(
        end_time, "%H:%M"
      ) - datetime.datetime.strptime(start_time, "%H:%M")
      delta_min = int(delta.total_seconds() / 60)
      if delta_min < 0:
        delta_min = 0
      action = activity.main_task + f" ({activity.subtask})"
      new_schedule += [[action, delta_min]]

    return new_schedule

  def __func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __func_clean_up(gpt_response, prompt)
      dur_sum = 0
      for act, dur in gpt_response:
        dur_sum += dur
        if str(type(act)) != "<class 'str'>":
          return False
        if str(type(dur)) != "<class 'int'>":
          return False

      time_range_str = (
        prompt.split(" originally planned schedule from ")[1]
        .split("\n")[0]
        .strip()
        .strip(":")
        .strip()
      )
      time_range = [
        datetime.datetime.strptime(time_str.strip(), "%H:%M %p")
        for time_str in time_range_str.split(" to ")
      ]
      delta_min = int((time_range[1] - time_range[0]).total_seconds() / 60)

      if int(dur_sum) != int(delta_min):
        return False

    except Exception:
      traceback.print_exc()
      return False
    return True

  def get_fail_safe(main_act_dur, truncated_act_dur):
    dur_sum = 0
    for _act, dur in main_act_dur:
      dur_sum += dur

    ret = truncated_act_dur[:]
    ret += main_act_dur[len(ret) - 1 :]

    # If there are excess, we need to trim...
    ret_dur_sum = 0
    count = 0
    over = None
    for _act, dur in ret:
      ret_dur_sum += dur
      if ret_dur_sum == dur_sum:
        break
      if ret_dur_sum > dur_sum:
        over = ret_dur_sum - dur_sum
        break
      count += 1

    if over:
      ret = ret[: count + 1]
      ret[-1][1] -= over

    return ret

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 10000,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(
    persona,
    main_act_dur,
    truncated_act_dur,
    start_time_hour,
    end_time_hour,
    inserted_act,
    inserted_act_dur,
    test_input,
  )
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe(main_act_dur, truncated_act_dur)
  output = safe_generate_structured_response(
    prompt, gpt_param, NewSchedule, 5, fail_safe, __func_validate, __func_clean_up
  )

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
