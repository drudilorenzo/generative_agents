from utils import debug
from typing import Any

from ..common import ActionLoc, openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts


def create_prompt(prompt_input: dict[str, Any]):
  persona_name = prompt_input["persona_name"]
  action_sector = prompt_input["action_sector"]
  accessible_arenas = prompt_input["accessible_arenas"]
  broad_action = prompt_input["broad_action"]
  specific_action = prompt_input["specific_action"]

  prompt = f"""
Jane Anderson is in kitchen in Jane Anderson's house.
Jane Anderson is going to Jane Anderson's house that has the following areas: [kitchen, bedroom, bathroom]
Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
For cooking, Jane Anderson should go to the following area in Jane Anderson's house:
Answer: kitchen
---
Tom Watson is in common room in Tom Watson's apartment.
Tom Watson is going to Hobbs Cafe that has the following areas: [cafe]
Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
For getting coffee, Tom Watson should go to the following area in Hobbs Cafe:
Answer: cafe
---
{persona_name} is going to {action_sector} that has the following areas: [{accessible_arenas}]
* Stay in the current area if the activity can be done there.
* NEVER go into other people's rooms unless necessary.
{persona_name} is {broad_action}. For {specific_action}, {persona_name} should go to the following area in {action_sector} (MUST pick one of [{accessible_arenas}]):
Answer:
  """
  return prompt


def run_gpt_prompt_action_arena(
  action_description,
  persona,
  act_world,
  act_sector,
  test_input=None,
  verbose=False,
):
  def create_prompt_input(
    action_description, persona, act_world, act_sector, test_input=None
  ):
    world_sector = f"{act_world}:{act_sector}"
    accessible_arena_str = persona.s_mem.get_str_accessible_sector_arenas(world_sector)
    curr = accessible_arena_str.split(", ")
    fin_accessible_arenas = []

    for i in curr:
      if "'s room" in i:
        if persona.scratch.last_name in i:
          fin_accessible_arenas += [i]
      else:
        fin_accessible_arenas += [i]
    accessible_arena_str = ", ".join(fin_accessible_arenas)

    action_description_1 = action_description
    action_description_2 = action_description
    if "(" in action_description:
      action_description_1 = action_description.split("(")[0].strip()
      action_description_2 = action_description.split("(")[-1][:-1]

    prompt_input = {
      "persona_name": persona.scratch.get_str_name(),
      "action_sector": act_sector,
      "accessible_arenas": accessible_arena_str,
      "broad_action": action_description_1,
      "specific_action": action_description_2,
    }

    return prompt_input

  def __func_clean_up(gpt_response: ActionLoc, prompt=""):
    return gpt_response.area

  def __func_validate(gpt_response, prompt=""):
    arena = __func_clean_up(gpt_response)
    if len(arena.strip()) < 1:
      return False
    if "}" in arena:
      return False
    if "," in arena:
      return False
    return True

  def get_fail_safe():
    fs = "main room"
    return fs

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 100,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(action_description, persona, act_world, act_sector)
  prompt = create_prompt(prompt_input)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt,
    gpt_param,
    ActionLoc,
    5,
    fail_safe,
    __func_validate,
    __func_clean_up,
    verbose=False,
  )

  # y = f"{act_world}:{act_sector}"
  # x = [i.strip() for i in persona.s_mem.get_str_accessible_sector_arenas(y).split(",")]
  # if output not in x:
  #   output = random.choice(x)

  if debug or verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
