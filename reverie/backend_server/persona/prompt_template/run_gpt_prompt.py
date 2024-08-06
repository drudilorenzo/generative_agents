"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: run_gpt_prompt.py
Description: Defines all run gpt prompt functions. These functions directly
interface with the safe_generate_response function.
"""
import re
import datetime
import sys
import ast

sys.path.append('../../')

from global_methods import *
from persona.prompt_template.gpt_structure import *
from persona.prompt_template.print_prompt import *

def get_random_alphanumeric(i=6, j=6): 
  """
  Returns a random alpha numeric strength that has the length of somewhere
  between i and j. 

  INPUT: 
    i: min_range for the length
    j: max_range for the length
  OUTPUT: 
    an alpha numeric str with the length of somewhere between i and j.
  """
  k = random.randint(i, j)
  x = ''.join(random.choices(string.ascii_letters + string.digits, k=k))
  return x

config_path = Path("../../llm_config.json")
with open(config_path, "r") as f:
    openai_config = json.load(f) 
model = openai_config["model"]

if "prompt_template" in openai_config:
    prompt_template = openai_config["prompt_template"]
else:
    prompt_template = "prompts_gpt"

prompt_dir = Path("./persona/prompt_template") / prompt_template 



##############################################################################
# CHAPTER 1: Run GPT Prompt
##############################################################################

def run_gpt_prompt_wake_up_hour(persona, test_input=None, verbose=False): 
  """
  Given the persona, returns an integer that indicates the hour when the 
  persona wakes up.  

  INPUT: 
    persona: The Persona class instance 
  OUTPUT: 
    integer for the wake up hour.
  """
  def create_prompt_input(persona, test_input=None): 
    if test_input: return test_input
    prompt_input = [persona.scratch.get_str_iss(),
                    persona.scratch.get_str_lifestyle(),
                    persona.scratch.get_str_firstname()]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    # Use regular expressions to find the first sequence of digits in the response
    match = re.search(r'\d+', gpt_response)
    cr = int(match.group(0))
    return cr
  
  def __func_validate(gpt_response, prompt=""): 
    try: 
      result = __func_clean_up(gpt_response, prompt="")
      int(result)
    except: 
      return False
    return True

  def get_fail_safe(): 
    fs = 8
    return fs

  # in general I need more max_tokens for llama3
  gpt_param = {"engine": model, "max_tokens": 3000, 
             "temperature": 0.8, "top_p": 1, "stream": False,
             "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  prompt_template = prompt_dir / "wake_up_hour.txt"
  prompt_input = create_prompt_input(persona, test_input)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()

  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  
  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
    
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_daily_plan(persona, 
                              wake_up_hour, 
                              test_input=None, 
                              verbose=False):
  """
  Basically the long term planning that spans a day. Returns a list of actions
  that the persona will take today. Usually comes in the following form: 
  'wake up and complete the morning routine at 6:00 am', 
  'eat breakfast at 7:00 am',.. 
  Note that the actions come without a period. 

  INPUT: 
    persona: The Persona class instance 
  OUTPUT: 
    a list of daily actions in broad strokes.
  """
  def create_prompt_input(persona, wake_up_hour, test_input=None):
    if test_input: return test_input
    prompt_input = []
    prompt_input += [persona.scratch.get_str_iss()]
    prompt_input += [persona.scratch.get_str_lifestyle()]
    prompt_input += [persona.scratch.get_str_curr_date_str()]
    prompt_input += [persona.scratch.get_str_firstname()]
    prompt_input += [f"{str(wake_up_hour)}:00 am"]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    # Split the response on '||' and strip whitespace
    activities = re.split(r'\|\||\n', gpt_response)
    cleaned_activities = [x for x in activities if len(x) > 3]  #no plan less than 4 letters
    return cleaned_activities

  def __func_validate(gpt_response, prompt=""):
    try: __func_clean_up(gpt_response, prompt="")
    except: 
      return False
    return True

  def get_fail_safe(): 
    fs = ['wake up and complete the morning routine at 6:00 am', 
          'eat breakfast at 7:00 am', 
          'read a book from 8:00 am to 12:00 pm', 
          'have lunch at 12:00 pm', 
          'take a nap from 1:00 pm to 4:00 pm', 
          'relax and watch TV from 7:00 pm to 8:00 pm', 
          'go to bed at 11:00 pm'] 
    return fs


  
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "daily_planning.txt"
  prompt_input = create_prompt_input(persona, wake_up_hour, test_input)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()

  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,  prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  output = ([f"wake up and complete the morning routine at {wake_up_hour}:00 am"]
              + output)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
    
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_generate_hourly_schedule(persona, 
                                            curr_hour_str,
                                            p_f_ds_hourly_org, 
                                            hour_str,
                                            intermission2=None,
                                            test_input=None, 
                                            verbose=False): 
  def create_prompt_input(persona, 
                          curr_hour_str, 
                          p_f_ds_hourly_org,
                          hour_str,
                          intermission2=None,
                          test_input=None): 
    if test_input: return test_input
    schedule_format = ""
    for i in hour_str: 
      schedule_format += f"[{persona.scratch.get_str_curr_date_str()} -- {i}]"
      schedule_format += f" Activity: [Fill in]\n"
    schedule_format = schedule_format[:-1]

    intermission_str = f"Here the originally intended hourly breakdown of"
    intermission_str += f" {persona.scratch.get_str_firstname()}'s schedule today: "
    for count, i in enumerate(persona.scratch.daily_req): 
      intermission_str += f"{str(count+1)}) {i}, "
    intermission_str = intermission_str[:-2]

    prior_schedule = ""
    if p_f_ds_hourly_org: 
      prior_schedule = "\n"
      for count, i in enumerate(p_f_ds_hourly_org): 
        prior_schedule += f"[(ID:{get_random_alphanumeric()})" 
        prior_schedule += f" {persona.scratch.get_str_curr_date_str()} --"
        prior_schedule += f" {hour_str[count]}] Activity:"
        prior_schedule += f" {persona.scratch.get_str_firstname()}"
        prior_schedule += f" is {i}\n"

    prompt_ending = f"[(ID:{get_random_alphanumeric()})"
    prompt_ending += f" {persona.scratch.get_str_curr_date_str()}"
    prompt_ending += f" -- {curr_hour_str}] Activity:"
    prompt_ending += f" {persona.scratch.get_str_firstname()} is"

    if intermission2: 
      intermission2 = f"\n{intermission2}"

    prompt_input = []
    prompt_input += [schedule_format]
    prompt_input += [persona.scratch.get_str_iss()]

    prompt_input += [prior_schedule + "\n"]
    prompt_input += [intermission_str]
    if intermission2: 
      prompt_input += [intermission2]
    else: 
      prompt_input += [""]
    prompt_input += [prompt_ending]

    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    if cr[-1] == ".":
      cr = cr[:-1]
    # in case the stupid AI decides to shove timestamps in remove it
    cr = cr.split("Activity:")[-1]
    cr = cr.split("]")[-1]
    cr = cr.replace('"','')
    return cr

  def __func_validate(gpt_response, prompt=""): 
    try: __func_clean_up(gpt_response, prompt="")
    except: return False
    return True

  def get_fail_safe(): 
    fs = "asleep"
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.5, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  prompt_template = prompt_dir / "generate_hourly_schedule.txt"
  prompt_input = create_prompt_input(persona, 
                                     curr_hour_str, 
                                     p_f_ds_hourly_org,
                                     hour_str, 
                                     intermission2,
                                     test_input)
  for i, prompt_value in enumerate(prompt_input):
    print("---- <INPUT {}> :".format(i), prompt_value)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()
  
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  
  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
    
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]








def run_gpt_prompt_task_decomp(persona, 
                               task, 
                               duration, 
                               test_input=None, 
                               verbose=False): 
  def create_prompt_input(persona, task, duration, test_input=None):
      
    curr_f_org_index = persona.scratch.get_f_daily_schedule_hourly_org_index()
    all_indices = []
    # if curr_f_org_index > 0: 
    #   all_indices += [curr_f_org_index-1]
    all_indices += [curr_f_org_index]
    if curr_f_org_index+1 <= len(persona.scratch.f_daily_schedule_hourly_org): 
      all_indices += [curr_f_org_index+1]
    if curr_f_org_index+2 <= len(persona.scratch.f_daily_schedule_hourly_org): 
      all_indices += [curr_f_org_index+2]

    curr_time_range = ""
    summ_str = f'Today is {persona.scratch.curr_time.strftime("%B %d, %Y")}. '
    summ_str += f'From '
    for index in all_indices: 
      if index < len(persona.scratch.f_daily_schedule_hourly_org): 
        start_min = 0
        for i in range(index): 
          start_min += persona.scratch.f_daily_schedule_hourly_org[i][1]
        end_min = start_min + persona.scratch.f_daily_schedule_hourly_org[index][1]
        start_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S") 
                      + datetime.timedelta(minutes=start_min)) 
        end_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S") 
                      + datetime.timedelta(minutes=end_min)) 
        start_time_str = start_time.strftime("%H:%M%p")
        end_time_str = end_time.strftime("%H:%M%p")
        summ_str += f"{start_time_str} ~ {end_time_str}, {persona.name} is planning on {persona.scratch.f_daily_schedule_hourly_org[index][0]}, "
        if curr_f_org_index+1 == index:
          curr_time_range = f'{start_time_str} ~ {end_time_str}'
    summ_str = summ_str[:-2] + "."

    prompt_input = []
    prompt_input += [persona.scratch.get_str_iss()]
    prompt_input += [summ_str]
    # prompt_input += [persona.scratch.get_str_curr_date_str()]
    prompt_input += [persona.scratch.get_str_firstname()]
    prompt_input += [persona.scratch.get_str_firstname()]
    prompt_input += [task]
    prompt_input += [curr_time_range]
    prompt_input += [duration]
    prompt_input += [persona.scratch.get_str_firstname()]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
        # Split the response into lines
    lines = gpt_response.strip().split('\n')
    
    # Define a regex pattern for extracting tasks
    task_pattern = re.compile(r"\d+\)(.*?) is (.*?)\(duration in minutes: (\d+)", re.DOTALL)
    
    # List to store decomposed tasks
    decomposed_tasks = []
    total_duration = 0
    
    # Process each line
    for line in lines:
      if re.match(r"\d+\)", line):  # Basic check for expected line structure
        match = task_pattern.search(line)
        if match:
          name, task, duration = match.groups()
          duration = int(duration)
          decomposed_tasks.append([task.strip(), duration])
          total_duration += duration
        else:
          pass
    
    return decomposed_tasks


  def __func_validate(gpt_response, prompt=""): 
    try: 
      result = __func_clean_up(gpt_response)
      str(result[0][0])
      int(result[0][1])
      for x in result:
        assert x[1] > 0
    except: 
      return False
    return True 

  def get_fail_safe(duration): 
    fs = ["nothing", duration]
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
             "temperature": 0.1, "top_p": 1, "stream": False,
             "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "task_decomp.txt"
  prompt_input = create_prompt_input(persona, task, duration)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(duration)

  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)


  fin_output = []
  time_sum = 0
  for i_task, i_duration in output: 
    time_sum += i_duration
    if time_sum <= duration: 
      fin_output += [[i_task, i_duration]]
    else: 
      break
  ftime_sum = 0
  for fi_task, fi_duration in fin_output: 
    ftime_sum += fi_duration
  
  # rescale times if allocated times don't match duration
  if ftime_sum != duration:
    duration_scale_factor = float(duration)/float(ftime_sum)
    for i in range(len(fin_output)):
      fin_output[i][1] *= duration_scale_factor
      
  output = fin_output 



  task_decomp = output
  ret = []
  for decomp_task, duration in task_decomp: 
    ret += [[f"{task} ({decomp_task})", duration]]
  output = ret


  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
    
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_action_sector(action_description, 
                                persona, 
                                maze, 
                                test_input=None, 
                                verbose=False):
  def create_prompt_input(action_description, persona, maze, test_input=None): 
    act_world = f"{maze.access_tile(persona.scratch.curr_tile)['world']}"
    accessible_sector_str = persona.s_mem.get_str_accessible_sectors(act_world)

    prompt_input = []
    
    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [persona.scratch.living_area.split(":")[1]]
    x = f"{act_world}:{persona.scratch.living_area.split(':')[1]}"
    prompt_input += [persona.s_mem.get_str_accessible_sector_arenas(x)]


    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"]
    x = f"{act_world}:{maze.access_tile(persona.scratch.curr_tile)['sector']}"
    prompt_input += [persona.s_mem.get_str_accessible_sector_arenas(x)]

    if persona.scratch.get_str_daily_plan_req() != "": 
      prompt_input += [f"\n{persona.scratch.get_str_daily_plan_req()}"]
    else: 
      prompt_input += [""]


    # MAR 11 TEMP
    accessible_sector_str = persona.s_mem.get_str_accessible_sectors(act_world)
    curr = accessible_sector_str.split(", ")
    fin_accessible_sectors = []
    for i in curr: 
      if "'s house" in i: 
        if persona.scratch.last_name in i: 
          fin_accessible_sectors += [i]
      else: 
        fin_accessible_sectors += [i]
    accessible_sector_str = ", ".join(fin_accessible_sectors)
    # END MAR 11 TEMP

    prompt_input += [accessible_sector_str]



    action_description_1 = action_description
    action_description_2 = action_description
    if "(" in action_description: 
      action_description_1 = action_description.split("(")[0].strip()
      action_description_2 = action_description.split("(")[-1][:-1]
    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [action_description_1]

    prompt_input += [action_description_2]
    prompt_input += [persona.scratch.get_str_name()]
    return prompt_input


  def __func_clean_up(gpt_response, prompt=""):
    # Clean the response from any surrounding formatting or unwanted characters
    cleaned_response = gpt_response.split("}")[0]
    cleaned_response = cleaned_response.split("{")[-1]
    cleaned_response = cleaned_response.replace("!","") #I get a lot of '!' in the simulation 
    cleaned_response = cleaned_response.strip().lower()  # Ensure it is in lower case for matching
  
    # should maybe have the locator and the room selector be the same function?
    def _extract_rooms(prompt):
      # Define the regex pattern to match the specific line and capture the list of rooms
      pattern = r'\(MUST pick one of \{([^}]*)\}\):'
    
      # Search for the pattern in the provided text
      match = re.search(pattern, prompt)
    
      if match:
        # Extract the list of rooms and split by comma to create a list
        rooms = match.group(1).split(', ')
        return rooms
      else:
        return []
  
    # Extract rooms from the prompt
    rooms = _extract_rooms(prompt)
  
    # Check each room in its original case to see if its lower case matches the cleaned response
    for room in rooms:
      if room.strip().lower() == cleaned_response:
        return room  # Return the original case of the matched room
    return None 

  #def __func_clean_up(gpt_response, prompt=""):
  #  cleaned_response = gpt_response.split("}")[0]
  #  cleaned_response = gpt_response.split("{")[-1]
  #  return cleaned_response

  def __func_validate(gpt_response, prompt=""): 
    return bool(__func_clean_up(gpt_response, prompt))
  
  def get_fail_safe(): 
    fs = ("Dummy string to be swapped out later")
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "action_location_sector.txt"
  prompt_input = create_prompt_input(action_description, persona, maze)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 10, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  world_name = f"{maze.access_tile(persona.scratch.curr_tile)['world']}"
  accesible_zones = [i.strip() for i in persona.s_mem.get_str_accessible_sectors(world_name).split(",")]

  if output not in accesible_zones: 
    new_zone = persona.scratch.living_area.split(":")[1]
    print(f"ERROR: {output} not in {accesible_zones} defaulting to: {new_zone} ")
    output = new_zone

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_action_arena(action_description, 
                                persona, 
                                maze, act_world, act_sector,
                                test_input=None, 
                                verbose=False):
  def create_prompt_input(action_description, persona, maze, act_world, act_sector, test_input=None): 
    prompt_input = []
    prompt_input += [persona.scratch.get_str_name()]
    x = f"{act_world}:{act_sector}"
    prompt_input += [act_sector]

    accessible_arena_str = persona.s_mem.get_str_accessible_sector_arenas(x)
    curr = accessible_arena_str.split(", ")
    fin_accessible_arenas = []
    for i in curr: 
      if "'s room" in i: 
        if persona.scratch.last_name in i: 
          fin_accessible_arenas += [i]
      else: 
        fin_accessible_arenas += [i]
    accessible_arena_str = ", ".join(fin_accessible_arenas)
    prompt_input += [accessible_arena_str]

    action_description_1 = action_description
    action_description_2 = action_description
    if "(" in action_description: 
      action_description_1 = action_description.split("(")[0].strip()
      action_description_2 = action_description.split("(")[-1][:-1]

    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [action_description_1]
    prompt_input += [action_description_2]
    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [act_sector]
    prompt_input += [accessible_arena_str]

    return prompt_input


  def __func_clean_up(gpt_response, prompt=""):
    # Clean the response from any surrounding formatting or unwanted characters
    cleaned_response = gpt_response.split("}")[0]
    cleaned_response = cleaned_response.split("{")[-1]
    cleaned_response = cleaned_response.strip().lower()  # Ensure it is in lower case for matching
  
    def _extract_rooms(prompt):
        # Define the regex pattern to match the specific line and capture the list of rooms
        pattern = r'\(MUST pick one of \{([^}]*)\}\):'
        
        # Search for the pattern in the provided text
        match = re.search(pattern, prompt)
        
        if match:
            # Extract the list of rooms
            rooms = match.group(1)
            # Split by comma and strip extra whitespace around room names
            rooms_list = [room.strip() for room in rooms.split(',')]
            return rooms_list
        else:
            return []
  
    # Extract rooms from the prompt
    rooms = _extract_rooms(prompt)
  
    # Check each room in its original case to see if its lower case matches the cleaned response
    for room in rooms:
      if room.strip().lower() == cleaned_response:
        return room  # Return the original case of the matched room
    return "" 

  def __func_validate(gpt_response, prompt=""): 
    return bool(__func_clean_up(gpt_response, prompt))
  
  def get_fail_safe(): 
    # NOTE this fail safe is not robust
    fs = ("kitchen")
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "action_location_object.txt"
  prompt_input = create_prompt_input(action_description, persona, maze, act_world, act_sector)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_action_game_object(action_description, 
                                      persona, 
                                      maze,
                                      temp_address,
                                      test_input=None, 
                                      verbose=False): 
  def create_prompt_input(action_description, 
                          persona, 
                          temp_address, 
                          test_input=None): 
    prompt_input = []
    if "(" in action_description: 
      action_description = action_description.split("(")[-1][:-1]
      
    prompt_input += [action_description]
    prompt_input += [persona
                     .s_mem.get_str_accessible_arena_game_objects(temp_address)]
    return prompt_input
  
  def __func_validate(gpt_response, prompt=""): 
    if len(gpt_response.strip()) < 1: 
      return False
    return True

  def __func_clean_up(gpt_response, prompt=""):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  def get_fail_safe(): 
    fs = ("bed")
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "action_object.txt"
  prompt_input = create_prompt_input(action_description, 
                                     persona, 
                                     temp_address, 
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  x = [i.strip() for i in persona.s_mem.get_str_accessible_arena_game_objects(temp_address).split(",")]
  if output not in x: 
    output = random.choice(x)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]




def run_gpt_prompt_pronunciatio(action_description, persona, verbose=False): 
  def create_prompt_input(action_description): 
    if "(" in action_description: 
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = [action_description]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    if len(cr) > 3:
      cr = cr[:3]
    return cr

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) == 0: 
        return False
    except: return False
    return True 

  def get_fail_safe(): 
    fs = "😋"
    return fs


  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    cr = gpt_response.strip()
    if len(cr) > 3:
      cr = cr[:3]
    return cr

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) == 0: 
        return False
    except: return False
    return True 

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 4") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "generate_pronunciatio.txt" ########
  prompt_input = create_prompt_input(action_description)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================

def run_gpt_prompt_event_triple(action_description, persona, verbose=False): 
  def create_prompt_input(action_description, persona): 
    if "(" in action_description: 
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = [persona.name, 
                    action_description,
                    persona.name]
    return prompt_input
  
  #def __func_clean_up(gpt_response, prompt=""):
  #  cr = gpt_response.strip()
  #  cr = [i.strip() for i in cr.split(")")[0].split("||")]
  #  if len(cr) == 3 and '(' in cr[0]:
  #    cr = cr[1:]
  #  return cr
  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    start_idx = cr.find("(")
    end_idx = cr.find(")")
    if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
      return []
    cr = cr[start_idx+1:end_idx].split("||")
    cr = [i.strip() for i in cr][1:3]
    return cr

  def __func_validate(gpt_response, prompt=""): 
    try: 
      gpt_response = __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) != 2: 
        return False
      for x in gpt_response:
        if len(x) < 2:
          return False
    except: return False
    return True 


  def get_fail_safe(persona): 
    fs = (persona.name, "is", "idle")
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None} 
  prompt_template = prompt_dir / "generate_event_triple.txt"
  prompt_input = create_prompt_input(action_description, persona)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(persona) ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  output = (persona.name, output[0], output[1])

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_thought_triple(thought, persona, verbose=False): 
  def create_prompt_input(thought, persona): 
    if "(" in thought: 
      thought = thought.split("(")[-1].split(")")[0]
    prompt_input = [persona.name, 
                    thought,
                    persona.name]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    start_idx = cr.find("(")
    end_idx = cr.find(")")
    if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
      return []
    cr = cr[start_idx+1:end_idx].split("||")
    cr = [i.strip() for i in cr][1:3]
    return cr

  def __func_validate(gpt_response, prompt=""): 
    try: 
      gpt_response = __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) != 2: 
        return False
      for x in gpt_response:
        if len(x) < 2:
          return False
    except: return False
    return True 


  def get_fail_safe(persona): 
    fs = (persona.name, "is", "idle")
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None} 
  prompt_template = prompt_dir / "generate_thought_triple.txt"
  prompt_input = create_prompt_input(thought, persona)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(persona) ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  output = (persona.name, output[0], output[1])

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]











def run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona, verbose=False): 
  def create_prompt_input(act_game_object, act_desp, persona): 
    prompt_input = [act_game_object, 
                    persona.name,
                    act_desp,
                    act_game_object,
                    act_game_object]
    return prompt_input

  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    cr = gpt_response.strip()
    if cr[-1] == ".": cr = cr[:-1]
    return cr

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      gpt_response = __func_clean_up(gpt_response, prompt="")
    except: 
      return False
    return True 

  def get_fail_safe(act_game_object): 
    fs = f"{act_game_object} is idle"
    return fs

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "generate_obj_event.txt" ########
  prompt_input = create_prompt_input(act_game_object, act_desp, persona)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(act_game_object) ########

  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_act_obj_event_triple(act_game_object, act_obj_desc, persona, verbose=False): 
  def create_prompt_input(act_game_object, act_obj_desc): 
    prompt_input = [act_game_object, 
                    act_obj_desc,
                    act_game_object]
    return prompt_input
  
  #def __func_clean_up(gpt_response, prompt=""):
  #  cr = gpt_response.strip()
  #  cr = [i.strip() for i in cr.split(")")[0].split("||")]
  #  if len(cr) == 3 and "(" in cr[0]:
  #    cr = cr[1:]
  #  return cr
  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    start_idx = cr.find("(")
    end_idx = cr.find(")")
    if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
      return []
    cr = cr[start_idx+1:end_idx].split("||")
    cr = [i.strip() for i in cr][1:3]
    return cr

  def __func_validate(gpt_response, prompt=""): 
    try: 
      gpt_response = __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) != 2: 
        return False
      for x in gpt_response:
        if len(x) < 2:
          return False
    except: return False
    return True 

  def get_fail_safe(act_game_object): 
    fs = (act_game_object, "is", "idle")
    return fs



  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "generate_action_obj_triple.txt"
  prompt_input = create_prompt_input(act_game_object, act_obj_desc)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(act_game_object)
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  output = (act_game_object, output[0], output[1])

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]





def run_gpt_prompt_new_decomp_schedule(persona, 
                                       main_act_dur, 
                                       truncated_act_dur, 
                                       start_time_hour,
                                       end_time_hour, 
                                       inserted_act,
                                       inserted_act_dur,
                                       test_input=None, 
                                       verbose=False): 
  def create_prompt_input(persona, 
                           main_act_dur, 
                           truncated_act_dur, 
                           start_time_hour,
                           end_time_hour, 
                           inserted_act,
                           inserted_act_dur,
                           test_input=None): 
    persona_name = persona.name
    start_hour_str = start_time_hour.strftime("%H:%M %p")
    end_hour_str = end_time_hour.strftime("%H:%M %p")

    original_plan = ""
    for_time = start_time_hour
    for i in main_act_dur: 
      original_plan += f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
      original_plan += "\n"
      for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init = ""
    for_time = start_time_hour
    for count, i in enumerate(truncated_act_dur): 
      new_plan_init += f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
      new_plan_init += "\n"
      if count < len(truncated_act_dur) - 1: 
        for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init += (for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M") + " ~"

    prompt_input = [persona_name, 
                    start_hour_str,
                    end_hour_str,
                    original_plan,
                    persona_name,
                    inserted_act,
                    inserted_act_dur,
                    persona_name,
                    start_hour_str,
                    end_hour_str,
                    end_hour_str,
                    new_plan_init]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    new_schedule = prompt + " " + gpt_response.strip()
    # llm really is weird about phrasing of revised schedule
    new_schedule = new_schedule.split("revised schedule:")[-1].strip()  
    new_schedule = new_schedule.split("\n")
  
    ret_temp = []
    for i in new_schedule:
      split_line =  i.split(" -- ")
      if len(split_line) > 1:
        ret_temp += [split_line]
 
    ret = []
    for time_str, action in ret_temp:
      start_time = time_str.split(" ~ ")[0].strip()
      end_time = time_str.split(" ~ ")[1].strip()
      delta = datetime.datetime.strptime(end_time, "%H:%M") - datetime.datetime.strptime(start_time, "%H:%M")
      delta_min = int(delta.total_seconds()/60)
      if delta_min < 0: delta_min = 0
      ret += [[action, delta_min]]
  
    return ret

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
      x = prompt.split("\n")[0].split("originally planned schedule from")[-1].strip()[:-1]
      x = [datetime.datetime.strptime(i.strip(), "%H:%M %p") for i in x.split(" to ")]
      delta_min = int((x[1] - x[0]).total_seconds()/60)

      if int(dur_sum) != int(delta_min): 
        return False

    except: 
      return False
    return True 

  def get_fail_safe(main_act_dur, truncated_act_dur): 
    dur_sum = 0
    for act, dur in main_act_dur: dur_sum += dur

    ret = truncated_act_dur[:]
    ret += main_act_dur[len(ret)-1:]

    # If there are access, we need to trim... 
    ret_dur_sum = 0
    count = 0
    over = None
    for act, dur in ret: 
      ret_dur_sum += dur
      if ret_dur_sum == dur_sum: 
        break
      if ret_dur_sum > dur_sum: 
        over = ret_dur_sum - dur_sum
        break
      count += 1 

    if over: 
      ret = ret[:count+1]
      ret[-1][1] -= over

    return ret

  # increased the temperature to prevent the llm getting 
  # 'stuck' trying the wrong answer over and over
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.8, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "new_decomp_schedule.txt"
  prompt_input = create_prompt_input(persona, 
                                     main_act_dur, 
                                     truncated_act_dur, 
                                     start_time_hour,
                                     end_time_hour, 
                                     inserted_act,
                                     inserted_act_dur,
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(main_act_dur, truncated_act_dur)
  # this task is unusually complicated so I give it more retries
  output = safe_generate_response(prompt, gpt_param, 20, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  
  # print ("* * * * output")
  # print (output)
  # print ('* * * * fail_safe')
  # print (fail_safe)



  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]






def run_gpt_prompt_decide_to_talk(persona, target_persona, retrieved,test_input=None, 
                                       verbose=False): 
  def create_prompt_input(init_persona, target_persona, retrieved, 
                          test_input=None): 
    last_chat = init_persona.a_mem.get_last_chat(target_persona.name)
    last_chatted_time = ""
    last_chat_about = ""
    if last_chat: 
      last_chatted_time = last_chat.created.strftime("%B %d, %Y, %H:%M:%S")
      last_chat_about = last_chat.description

    context = ""
    for c_node in retrieved["events"]: 
      curr_desc = c_node.description.split(" ")
      curr_desc[2:3] = ["was"]
      curr_desc = " ".join(curr_desc)
      context +=  f"{curr_desc}. "
    context += "\n"
    for c_node in retrieved["thoughts"]: 
      context +=  f"{c_node.description}. "

    curr_time = init_persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
    init_act_desc = init_persona.scratch.act_description
    if "(" in init_act_desc: 
      init_act_desc = init_act_desc.split("(")[-1][:-1]
    
    if len(init_persona.scratch.planned_path) == 0 and "waiting" not in init_act_desc: 
      init_p_desc = f"{init_persona.name} is already {init_act_desc}"
    elif "waiting" in init_act_desc:
      init_p_desc = f"{init_persona.name} is {init_act_desc}"
    else: 
      init_p_desc = f"{init_persona.name} is on the way to {init_act_desc}"

    target_act_desc = target_persona.scratch.act_description
    if "(" in target_act_desc: 
      target_act_desc = target_act_desc.split("(")[-1][:-1]
    
    if len(target_persona.scratch.planned_path) == 0 and "waiting" not in init_act_desc: 
      target_p_desc = f"{target_persona.name} is already {target_act_desc}"
    elif "waiting" in init_act_desc:
      target_p_desc = f"{init_persona.name} is {init_act_desc}"
    else: 
      target_p_desc = f"{target_persona.name} is on the way to {target_act_desc}"


    prompt_input = []
    prompt_input += [context]

    prompt_input += [curr_time]

    prompt_input += [init_persona.name]
    prompt_input += [target_persona.name]
    prompt_input += [last_chatted_time]
    prompt_input += [last_chat_about]


    prompt_input += [init_p_desc]
    prompt_input += [target_p_desc]
    prompt_input += [init_persona.name]
    prompt_input += [target_persona.name]
    return prompt_input
  
  def __func_validate(gpt_response, prompt=""):
      try:
          response = gpt_response.split("Answer in yes or no:")[-1].strip().lower()
          if "yes" in response or "no" in response:
              return True
          return False
      except:
          return False
  
  def __func_clean_up(gpt_response, prompt=""):
      response = gpt_response.split("Answer in yes or no:")[-1].strip().lower()
      
      # Find the positions of 'yes' and 'no' in the response
      pos_yes = response.find("yes")
      pos_no = response.find("no")
      
      # Determine which keyword appears first and return that word
      if pos_yes == -1 and pos_no == -1:
          return "invalid"  # Neither 'yes' nor 'no' found
      elif pos_no == -1 or (pos_yes != -1 and pos_yes < pos_no):
          return "yes"  # 'Yes' is found and either 'no' is not found or 'yes' comes first
      else:
          return "no"  # 'No' is found and it comes before 'yes'


  def get_fail_safe(): 
    fs = "yes"
    return fs



  #gpt_param = {"engine": model, "max_tokens": 3000, 
  #             "temperature": 0, "top_p": 1, "stream": False,
  #             "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  gpt_param = {"engine": model, "max_tokens": 3000, 
             "temperature": 0.8, "top_p": 1, "stream": False,
             "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "decide_to_talk.txt"
  prompt_input = create_prompt_input(persona, target_persona, retrieved,
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]




def run_gpt_prompt_decide_to_react(persona, target_persona, retrieved,test_input=None, 
                                       verbose=False): 
  def create_prompt_input(init_persona, target_persona, retrieved, 
                          test_input=None): 

    


    context = ""
    for c_node in retrieved["events"]: 
      curr_desc = c_node.description.split(" ")
      curr_desc[2:3] = ["was"]
      curr_desc = " ".join(curr_desc)
      context +=  f"{curr_desc}. "
    context += "\n"
    for c_node in retrieved["thoughts"]: 
      context +=  f"{c_node.description}. "

    curr_time = init_persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
    init_act_desc = init_persona.scratch.act_description
    if "(" in init_act_desc: 
      init_act_desc = init_act_desc.split("(")[-1][:-1]
    if len(init_persona.scratch.planned_path) == 0: 
      loc = ""
      if ":" in init_persona.scratch.act_address:
        loc = init_persona.scratch.act_address.split(":")[-1] + " in " + init_persona.scratch.act_address.split(":")[-2]
      init_p_desc = f"{init_persona.name} is already {init_act_desc} at {loc}"
    else: 
      loc = ""
      if ":" in init_persona.scratch.act_address:
        loc = init_persona.scratch.act_address.split(":")[-1] + " in " + init_persona.scratch.act_address.split(":")[-2]
      init_p_desc = f"{init_persona.name} is on the way to {init_act_desc} at {loc}"

    target_act_desc = target_persona.scratch.act_description
    if "(" in target_act_desc: 
      target_act_desc = target_act_desc.split("(")[-1][:-1]
    if len(target_persona.scratch.planned_path) == 0: 
      loc = ""
      if ":" in target_persona.scratch.act_address:
        loc = target_persona.scratch.act_address.split(":")[-1] + " in " + target_persona.scratch.act_address.split(":")[-2]
      target_p_desc = f"{target_persona.name} is already {target_act_desc} at {loc}"
    else: 
      loc = ""
      if ":" in target_persona.scratch.act_address:
        loc = target_persona.scratch.act_address.split(":")[-1] + " in " + target_persona.scratch.act_address.split(":")[-2]
      target_p_desc = f"{target_persona.name} is on the way to {target_act_desc} at {loc}"

    prompt_input = []
    prompt_input += [context]
    prompt_input += [curr_time]
    prompt_input += [init_p_desc]
    prompt_input += [target_p_desc]

    prompt_input += [init_persona.name]
    prompt_input += [init_act_desc]
    prompt_input += [target_persona.name]
    prompt_input += [target_act_desc]

    prompt_input += [init_act_desc]
    return prompt_input
  
  # Define the improved validation and clean-up functions
  def __func_validate(gpt_response, prompt=""):
    try:
      # Search for the pattern "Answer: Option X" where X is 1 or 2
      match = re.search(r"Answer: Option\s+([12])", gpt_response)
      # If a match is found and the number is directly following "Answer: Option"
      if match:
        return True
      else:
        return False
    except Exception as e:
      # Log the error or handle it as needed
      print(f"Error during validation: {e}")
      return False
  
  def __func_clean_up(gpt_response, prompt=""):
    match = re.search(r"Answer: Option\s+([12])", gpt_response)
    return match.group(1)  # Return the number (1 or 2)


  def get_fail_safe(): 
    fs = "1"
    return fs


  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "decide_to_react.txt"
  prompt_input = create_prompt_input(persona, target_persona, retrieved,
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]

















def run_gpt_prompt_create_conversation(persona, target_persona, curr_loc,
                                       test_input=None, verbose=False): 
  def create_prompt_input(init_persona, target_persona, curr_loc, 
                          test_input=None): 

    prev_convo_insert = "\n"
    if init_persona.a_mem.seq_chat: 
      for i in init_persona.a_mem.seq_chat: 
        if i.object == target_persona.scratch.name: 
          v1 = int((init_persona.scratch.curr_time - i.created).total_seconds()/60)
          prev_convo_insert += f'{str(v1)} minutes ago, they had the following conversation.\n'
          for row in i.filling: 
            prev_convo_insert += f'{row[0]}: "{row[1]}"\n'
          break
    if prev_convo_insert == "\n": 
      prev_convo_insert = ""
    if init_persona.a_mem.seq_chat: 
      if int((init_persona.scratch.curr_time - init_persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480: 
        prev_convo_insert = ""


    init_persona_thought_nodes = init_persona.a_mem.retrieve_relevant_thoughts(target_persona.scratch.act_event[0],
                                target_persona.scratch.act_event[1],
                                target_persona.scratch.act_event[2])
    init_persona_thought = ""
    for i in init_persona_thought_nodes: 
      init_persona_thought += f"-- {i.description}\n"

    target_persona_thought_nodes = target_persona.a_mem.retrieve_relevant_thoughts(init_persona.scratch.act_event[0],
                                init_persona.scratch.act_event[1],
                                init_persona.scratch.act_event[2])
    target_persona_thought = ""
    for i in target_persona_thought_nodes: 
      target_persona_thought += f"-- {i.description}\n"

    init_persona_curr_desc = ""
    if init_persona.scratch.planned_path: 
      init_persona_curr_desc = f"{init_persona.name} is on the way to {init_persona.scratch.act_description}"
    else: 
      init_persona_curr_desc = f"{init_persona.name} is {init_persona.scratch.act_description}"

    target_persona_curr_desc = ""
    if target_persona.scratch.planned_path: 
      target_persona_curr_desc = f"{target_persona.name} is on the way to {target_persona.scratch.act_description}"
    else: 
      target_persona_curr_desc = f"{target_persona.name} is {target_persona.scratch.act_description}"
 

    curr_loc = curr_loc["arena"]

    prompt_input = []
    prompt_input += [init_persona.scratch.get_str_iss()]
    prompt_input += [target_persona.scratch.get_str_iss()]

    prompt_input += [init_persona.name]
    prompt_input += [target_persona.name]
    prompt_input += [init_persona_thought]

    prompt_input += [target_persona.name]
    prompt_input += [init_persona.name]
    prompt_input += [target_persona_thought]

    prompt_input += [init_persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S")]

    prompt_input += [init_persona_curr_desc]
    prompt_input += [target_persona_curr_desc]

    prompt_input += [prev_convo_insert]

    prompt_input += [init_persona.name]
    prompt_input += [target_persona.name]

    prompt_input += [curr_loc]
    prompt_input += [init_persona.name]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    # print ("???")
    # print (gpt_response)


    gpt_response = (prompt + gpt_response).split("What would they talk about now?")[-1].strip()
    content = re.findall('"([^"]*)"', gpt_response)

    speaker_order = []
    for i in gpt_response.split("\n"): 
      name = i.split(":")[0].strip() 
      if name: 
        speaker_order += [name]

    ret = []
    for count, speaker in enumerate(speaker_order): 
      ret += [[speaker, content[count]]]

    return ret

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(init_persona, target_persona): 
    convo = [[init_persona.name, "Hi!"], 
             [target_persona.name, "Hi!"]]
    return convo


  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "create_conversation.txt"
  prompt_input = create_prompt_input(persona, target_persona, curr_loc, 
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe(persona, target_persona)
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]










def run_gpt_prompt_summarize_conversation(persona, conversation, test_input=None, verbose=False): 
  def create_prompt_input(conversation, test_input=None): 
    convo_str = ""
    for row in conversation: 
      convo_str += f'{row[0]}: "{row[1]}"\n'

    prompt_input = [convo_str]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    ret = "conversing about " + gpt_response.strip()
    return ret

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return "conversing with a housemate about morning greetings"


  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    ret = "conversing about " + gpt_response.strip()
    return ret

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 


  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 11") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "summarize_conversation.txt" ########
  prompt_input = create_prompt_input(conversation, test_input)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_extract_keywords(persona, description, test_input=None, verbose=False): 
  def create_prompt_input(description, test_input=None): 
    if "\n" in description: 
      description = description.replace("\n", " <LINE_BREAK> ")
    prompt_input = [description]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = gpt_response.strip().split("Emotive keywords:")
    factual = [i.strip() for i in gpt_response[0].split(",")]
    emotive = [i.strip() for i in gpt_response[1].split(",")]
    all_keywords = factual + emotive
    ret = []
    for i in all_keywords: 
      if i: 
        i = i.lower()
        if i[-1] == ".": 
          i = i[:-1]
        ret += [i]
    return set(ret)

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return []

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "get_keywords.txt"
  prompt_input = create_prompt_input(description, test_input)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)


  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_keyword_to_thoughts(persona, keyword, concept_summary, test_input=None, verbose=False): 
  def create_prompt_input(persona, keyword, concept_summary, test_input=None): 
    prompt_input = [keyword, concept_summary, persona.name]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = gpt_response.strip()
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return ""

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "keyword_to_thoughts.txt"
  prompt_input = create_prompt_input(persona, keyword, concept_summary)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]









def run_gpt_prompt_convo_to_thoughts(persona, 
                                    init_persona_name,  
                                    target_persona_name,
                                    convo_str,
                                    fin_target, test_input=None, verbose=False): 
  def create_prompt_input(init_persona_name,  
                                    target_persona_name,
                                    convo_str,
                                    fin_target, test_input=None): 
    prompt_input = [init_persona_name,
                    target_persona_name,
                    convo_str,
                    init_persona_name,
                    fin_target]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = gpt_response.strip()
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return ""

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "convo_to_thoughts.txt"
  prompt_input = create_prompt_input(init_persona_name,  
                                    target_persona_name,
                                    convo_str,
                                    fin_target)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



























def run_gpt_prompt_event_poignancy(persona, event_description, test_input=None, verbose=False): 
  def create_prompt_input(persona, event_description, test_input=None): 
    prompt_input = [persona.scratch.name,
                    persona.scratch.get_str_iss(),
                    persona.scratch.name,
                    event_description]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = int(gpt_response.strip())
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return 1 # just going to ignore things that we can't understand



  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""):
    # Search for the first sequence of digits in the gpt_response
    match = re.search(r'\d+', gpt_response)
    result = int(match.group())
    return result 

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      result = int(__func_clean_up(gpt_response, prompt))
      if result < 1 or result > 10:
        return False
      return True
    except:
      return False 

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 7") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "poignancy_event.txt" ########
  prompt_input = create_prompt_input(persona, event_description)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  # I could not get GPT to json here for some reason...
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================

def run_gpt_prompt_thought_poignancy(persona, event_description, test_input=None, verbose=False): 
  def create_prompt_input(persona, event_description, test_input=None): 
    prompt_input = [persona.scratch.name,
                    persona.scratch.get_str_iss(),
                    persona.scratch.name,
                    event_description]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = int(gpt_response.strip())
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return 4

  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    gpt_response = int(gpt_response)
    return gpt_response

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 8") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "poignancy_thought.txt" ########
  prompt_input = create_prompt_input(persona, event_description)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_chat_poignancy(persona, event_description, test_input=None, verbose=False): 
  def create_prompt_input(persona, event_description, test_input=None): 
    prompt_input = [persona.scratch.name,
                    persona.scratch.get_str_iss(),
                    persona.scratch.name,
                    event_description]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = int(gpt_response.strip())
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return 4




  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    gpt_response = int(gpt_response)
    return gpt_response

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 9") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "poignancy_chat.txt" ########
  prompt_input = create_prompt_input(persona, event_description)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_focal_pt(persona, statements, n, test_input=None, verbose=False): 
  def create_prompt_input(persona, statements, n, test_input=None): 
    prompt_input = [statements, str(n)]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = "1) " + gpt_response.strip()
    ret = []
    for i in gpt_response.split("\n"): 
      ret += [i.split(") ")[-1]]
    return ret

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(n): 
    return ["Who am I"] * n


  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    begin_index = begin_index = gpt_response.find("BEGIN") + len("BEGIN")
    end_index =  gpt_response.find("END")
    content = gpt_response[begin_index:end_index].strip()
    ret = [x.strip().replace("\n"," ") for x in content.split(",")[0:3]]
    return ret

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 


  #print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 12") ########
  #gpt_param = {"engine": model, "max_tokens": 3000, 
  #             "temperature": 0.1, "top_p": 1, "stream": False,
  #             "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  #prompt_template = prompt_dir / "generate_focal_pt.txt" ########
  #prompt_input = create_prompt_input(persona, statements, n)  ########
  #prompt = generate_prompt(prompt_input, prompt_template)
  #example_output = '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]' ########
  #special_instruction = "Output must be a list of str." ########
  #fail_safe = get_fail_safe(n) ########
  #output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 5, fail_safe, prompt_input,
  #                                        __chat_func_validate, __chat_func_clean_up, True)
  #if output != False: 
  #  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  ## ChatGPT Plugin ===========================================================

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "generate_focal_pt.txt"
  prompt_input = create_prompt_input(persona, statements, n)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe(n)
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]




  
def run_gpt_prompt_insight_and_guidance(persona, statements, n, test_input=None, verbose=False): 
  def create_prompt_input(persona, statements, n, test_input=None): 
    prompt_input = [statements, str(n)]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    ret = dict()
    for line in gpt_response.split("\n"): 
      if re.match(r"^\s*insight", line.strip(), re.IGNORECASE):
        pass
      else:
        continue
      row = line.split("||")[-1]
      thought = row.split("(because of ")[0].strip()
      evi_raw = row.split("(because of ")[1].split(")")[0].strip()
      evi_raw = re.findall(r'\d+', evi_raw)
      evi_raw = [int(i.strip()) for i in evi_raw]
      ret[thought] = evi_raw
    return ret

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(n): 
    return ["nothing",[0]] * n




  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.5, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "insight_and_evidence.txt"
  prompt_input = create_prompt_input(persona, statements, n)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe(n)
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]








def run_gpt_prompt_agent_chat_summarize_ideas(persona, target_persona, statements, curr_context, test_input=None, verbose=False): 
  def create_prompt_input(persona, target_persona, statements, curr_context, test_input=None): 
    prompt_input = [persona.scratch.get_str_curr_date_str(), curr_context, persona.scratch.currently, 
                    statements, persona.scratch.name, target_persona.scratch.name]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return "..."


  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    return gpt_response.split('"')[0].strip()

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 17") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "summarize_chat_ideas.txt" ########
  prompt_input = create_prompt_input(persona, target_persona, statements, curr_context)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_agent_chat_summarize_relationship(persona, target_persona, statements, test_input=None, verbose=False): 
  def create_prompt_input(persona, target_persona, statements, test_input=None): 
    prompt_input = [statements, persona.scratch.name, target_persona.scratch.name]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return "..."


  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    return gpt_response.split('"')[0].strip()

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 18") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "summarize_chat_relationship.txt" ########
  prompt_input = create_prompt_input(persona, target_persona, statements)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_agent_chat(maze, persona, target_persona,
                               curr_context, 
                               init_summ_idea, 
                               target_summ_idea, test_input=None, verbose=False): 
  def create_prompt_input(persona, target_persona, curr_context, init_summ_idea, target_summ_idea, test_input=None): 
    prev_convo_insert = "\n"
    if persona.a_mem.seq_chat: 
      for i in persona.a_mem.seq_chat: 
        if i.object == target_persona.scratch.name: 
          v1 = int((persona.scratch.curr_time - i.created).total_seconds()/60)
          prev_convo_insert += f'{str(v1)} minutes ago, {persona.scratch.name} and {target_persona.scratch.name} were already {i.description} This context takes place after that conversation.'
          break
    if prev_convo_insert == "\n": 
      prev_convo_insert = ""
    if persona.a_mem.seq_chat: 
      if int((persona.scratch.curr_time - persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480: 
        prev_convo_insert = ""
    print (prev_convo_insert)

    curr_sector = f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"
    curr_arena= f"{maze.access_tile(persona.scratch.curr_tile)['arena']}"
    curr_location = f"{curr_arena} in {curr_sector}"
    

    prompt_input = [persona.scratch.currently, 
                    target_persona.scratch.currently, 
                    prev_convo_insert,
                    curr_context, 
                    curr_location,

                    persona.scratch.name,
                    init_summ_idea, 
                    persona.scratch.name,
                    target_persona.scratch.name,

                    target_persona.scratch.name,
                    target_summ_idea, 
                    target_persona.scratch.name,
                    persona.scratch.name,

                    persona.scratch.name]
    return prompt_input
  
  ## this is not getting used?
  #def __func_clean_up(gpt_response, prompt=""):
  #  print (gpt_response)

  #  gpt_response = (prompt + gpt_response).split("Here is their conversation.")[-1].strip()
  #  content = re.findall('"([^"]*)"', gpt_response)

  #  speaker_order = []
  #  for i in gpt_response.split("\n"): 
  #    name = i.split(":")[0].strip() 
  #    if name: 
  #      speaker_order += [name]

  #  ret = []
  #  for count, speaker in enumerate(speaker_order): 
  #    ret += [[speaker, content[count]]]

  #  return ret



  def get_fail_safe(): 
    return []

  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    start_index = gpt_response.rfind('{')
    end_index = gpt_response.rfind('}') + 1
    curr_gpt_response = gpt_response[start_index:end_index]
    curr_gpt_response = json.loads(curr_gpt_response)["output"]
    return curr_gpt_response

  def __func_validate(gpt_response, prompt=""): ############
    try:
      cleaned = __func_clean_up(gpt_response)
      for x in cleaned:
        assert len(x) == 2
      return True
    except:
      return False

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "agent_chat.txt" ########
  prompt_input = create_prompt_input(persona, target_persona, curr_context, init_summ_idea, target_summ_idea)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_summarize_ideas(persona, statements, question, test_input=None, verbose=False): 
  def create_prompt_input(persona, statements, question, test_input=None): 
    prompt_input = [statements, persona.scratch.name, question]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    return gpt_response.split('"')[0].strip()

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return "..."


  # ChatGPT Plugin ===========================================================
  def __func_clean_up(gpt_response, prompt=""): ############
    return gpt_response

  def __func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "summarize_ideas.txt" ########
  prompt_input = create_prompt_input(persona, statements, question)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_generate_next_convo_line(persona, interlocutor_desc, prev_convo, retrieved_summary, test_input=None, verbose=False): 
  def create_prompt_input(persona, interlocutor_desc, prev_convo, retrieved_summary, test_input=None): 
    prompt_input = [persona.scratch.name, 
                    persona.scratch.get_str_iss(),
                    persona.scratch.name, 
                    interlocutor_desc, 
                    prev_convo, 
                    persona.scratch.name,
                    retrieved_summary, 
                    persona.scratch.name,]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    return gpt_response.split('"')[0].strip()

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return "..."

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "generate_next_convo_line.txt"
  prompt_input = create_prompt_input(persona, interlocutor_desc, prev_convo, retrieved_summary)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_generate_whisper_inner_thought(persona, whisper, test_input=None, verbose=False): 
  def create_prompt_input(persona, whisper, test_input=None): 
    prompt_input = [persona.scratch.name, whisper]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    return gpt_response.split('"')[0].strip()

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return "..."

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "whisper_inner_thought.txt"
  prompt_input = create_prompt_input(persona, whisper)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_planning_thought_on_convo(persona, all_utt, test_input=None, verbose=False): 
  def create_prompt_input(persona, all_utt, test_input=None): 
    prompt_input = [all_utt, persona.scratch.name, persona.scratch.name, persona.scratch.name]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    return gpt_response.split('"')[0].strip()

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return "..."

  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "planning_thought_on_convo.txt"
  prompt_input = create_prompt_input(persona, all_utt)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_memo_on_convo(persona, all_utt, test_input=None, verbose=False): 
  def create_prompt_input(persona, all_utt, test_input=None): 
    prompt_input = [all_utt, persona.scratch.name, persona.scratch.name, persona.scratch.name]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""): ############
    start_index = gpt_response.rfind('{')
    end_index = gpt_response.rfind('}') + 1
    curr_gpt_response = gpt_response[start_index:end_index]
    curr_gpt_response = json.loads(curr_gpt_response)["output"]
    return curr_gpt_response

  def __func_validate(gpt_response, prompt=""): ############
    try:
      __func_clean_up(gpt_response)
      return True
    except:
      return False


  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 15") ########
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = prompt_dir / "memo_on_convo.txt" ########
  prompt_input = create_prompt_input(persona, all_utt)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = "" ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)

  if debug or verbose: 
    print_run_prompts(prompt_template, persona, gpt_param, 
                      prompt_input, prompt, output)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]




def run_gpt_generate_safety_score(persona, comment, test_input=None, verbose=False): 
  def create_prompt_input(comment, test_input=None):
    prompt_input = [comment]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""): 
    match = re.search(r'\d+', gpt_response)
    cr = int(match.group(0))
    return cr

  def __func_validate(gpt_response, prompt=""): 
    try: 
      int(__func_clean_up(gpt_response))
      return True
    except:
      return False 

  def get_fail_safe():
    return None

  prompt_template = prompt_dir / "anthromorphosization.txt" 
  prompt_input = create_prompt_input(comment) 
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() 
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 0.1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  # I don't want the simulation to crash because I think its too real
  output=1
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def extract_first_json_dict(data_str):
    # Find the first occurrence of a JSON object within the string
    start_idx = data_str.find('{')
    end_idx = data_str.find('}', start_idx) + 1

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
        # If parsing fails, return None
        return None


def run_gpt_generate_iterative_chat_utt(maze, init_persona, target_persona, retrieved, curr_context, curr_chat, test_input=None, verbose=False): 
  def create_prompt_input(maze, init_persona, target_persona, retrieved, curr_context, curr_chat, test_input=None):
    persona = init_persona
    prev_convo_insert = "\n"
    if persona.a_mem.seq_chat: 
      for i in persona.a_mem.seq_chat: 
        if i.object == target_persona.scratch.name: 
          v1 = int((persona.scratch.curr_time - i.created).total_seconds()/60)
          prev_convo_insert += f'{str(v1)} minutes ago, {persona.scratch.name} and {target_persona.scratch.name} were already {i.description} This context takes place after that conversation.'
          break
    if prev_convo_insert == "\n": 
      prev_convo_insert = ""
    if persona.a_mem.seq_chat: 
      if int((persona.scratch.curr_time - persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480: 
        prev_convo_insert = ""
    print (prev_convo_insert)

    curr_sector = f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"
    curr_arena= f"{maze.access_tile(persona.scratch.curr_tile)['arena']}"
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

    init_iss = f"Here is Here is a brief description of {init_persona.scratch.name}.\n{init_persona.scratch.get_str_iss()}"
    prompt_input = [init_iss, init_persona.scratch.name, retrieved_str, prev_convo_insert,
      curr_location, curr_context, init_persona.scratch.name, target_persona.scratch.name,
      convo_str, init_persona.scratch.name, target_persona.scratch.name,
      init_persona.scratch.name, init_persona.scratch.name,
      init_persona.scratch.name
      ]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""): 
    gpt_response = extract_first_json_dict(gpt_response)

    cleaned_dict = dict()
    cleaned = []
    for key, val in gpt_response.items(): 
      cleaned += [val]
    cleaned_dict["utterance"] = cleaned[0]
    cleaned_dict["end"] = True
    if "f" in str(cleaned[1]) or "F" in str(cleaned[1]): 
      cleaned_dict["end"] = False

    return cleaned_dict

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response)
      return True
    except:
      return False 

  def get_fail_safe():
    cleaned_dict = dict()
    cleaned_dict["utterance"] = "..."
    cleaned_dict["end"] = False
    return cleaned_dict

  prompt_template = prompt_dir / "iterative_convo.txt" 
  prompt_input = create_prompt_input(maze, init_persona, target_persona, retrieved, curr_context, curr_chat) 
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe() 
  gpt_param = {"engine": model, "max_tokens": 3000, 
               "temperature": 1, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe, prompt_input, prompt_template,
                                   __func_validate, __func_clean_up)
  
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
