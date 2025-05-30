"""
Author: Joon Sung Park (joonspk@stanford.edu)
File: views.py
"""
import os
import json

import datetime
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from global_methods import check_if_file_exists, find_filenames
from django.conf import settings

if settings.USE_MQTT:
  from .mqtt_client import DjangoMQTTClient, MQTTConnectionError
from django.views.decorators.csrf import csrf_exempt

fs_temp_storage = "temp_storage"

# Initialize MQTT client only if MQTT is enabled
mqtt_client = None
if settings.USE_MQTT:
  try:
    mqtt_client = DjangoMQTTClient()
    mqtt_client.connect()
  except MQTTConnectionError as e:
    raise RuntimeError(f"Failed to initialize MQTT client: {e}")

# Store movement data temporarily
movement_data = {}

def _handle_movement_update(data):
  """Handle movement updates from backend via MQTT."""
  global movement_data
  movement_data = data


def landing(request): 
  context = {}
  template = "landing/landing.html"
  return render(request, template, context)


def demo(request, sim_code, step, play_speed="2"): 
  move_file = f"compressed_storage/{sim_code}/master_movement.json"
  meta_file = f"compressed_storage/{sim_code}/meta.json"
  step = int(step)
  play_speed_opt = {"1": 1, "2": 2, "3": 4,
                    "4": 8, "5": 16, "6": 32}
  if play_speed not in play_speed_opt:
    play_speed = 2
  else:
    play_speed = play_speed_opt[play_speed]

  # Loading the basic meta information about the simulation.
  meta = dict() 
  with open (meta_file) as json_file: 
    meta = json.load(json_file)

  sec_per_step = meta["sec_per_step"]
  start_datetime = datetime.datetime.strptime(meta["start_date"] + " 00:00:00", 
                                              '%B %d, %Y %H:%M:%S')
  for i in range(step): 
    start_datetime += datetime.timedelta(seconds=sec_per_step)
  start_datetime = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")

  # Loading the movement file
  raw_all_movement = dict()
  with open(move_file) as json_file: 
    raw_all_movement = json.load(json_file)
 
  # Loading all names of the personas
  persona_names = dict()
  persona_names = []
  persona_names_set = set()
  for p in list(raw_all_movement["0"].keys()): 
    persona_names += [{"original": p, 
                       "underscore": p.replace(" ", "_"), 
                       "initial": p[0] + p.split(" ")[-1][0]}]
    persona_names_set.add(p)

  # <all_movement> is the main movement variable that we are passing to the 
  # frontend. Whereas we use ajax scheme to communicate steps to the frontend
  # during the simulation stage, for this demo, we send all movement 
  # information in one step. 
  all_movement = dict()

  # Preparing the initial step. 
  # <init_prep> sets the locations and descriptions of all agents at the
  # beginning of the demo determined by <step>. 
  init_prep = dict() 
  for int_key in range(step+1): 
    key = str(int_key)
    val = raw_all_movement[key]
    for p in persona_names_set: 
      if p in val: 
        init_prep[p] = val[p]
  persona_init_pos = dict()
  for p in persona_names_set: 
    persona_init_pos[p.replace(" ","_")] = init_prep[p]["movement"]
  all_movement[step] = init_prep

  # Finish loading <all_movement>
  for int_key in range(step+1, len(raw_all_movement.keys())): 
    all_movement[int_key] = raw_all_movement[str(int_key)]

  context = {"sim_code": sim_code,
             "step": step,
             "persona_names": persona_names,
             "persona_init_pos": json.dumps(persona_init_pos), 
             "all_movement": json.dumps(all_movement), 
             "start_datetime": start_datetime,
             "sec_per_step": sec_per_step,
             "play_speed": play_speed,
             "mode": "demo"}
  template = "demo/demo.html"

  return render(request, template, context)


def UIST_Demo(request): 
  return demo(request, "March20_the_ville_n25_UIST_RUN-step-1-141", 2160, play_speed="3")


def home(request):
  f_curr_sim_code = f"{fs_temp_storage}/curr_sim_code.json"
  f_curr_step = f"{fs_temp_storage}/curr_step.json"

  if not check_if_file_exists(f_curr_step) or not check_if_file_exists(f_curr_sim_code): 
    context = {}
    template = "home/error_start_backend.html"
    return render(request, template, context)

  with open(f_curr_sim_code) as json_file:  
    sim_code = json.load(json_file)["sim_code"]
  
  with open(f_curr_step) as json_file:  
    step = json.load(json_file)["step"]

  persona_names = []
  persona_names_set = set()
  for filepath in find_filenames(f"storage/{sim_code}/personas", ""): 
    if os.path.isdir(filepath):
      x = filepath.split("/")[-1].strip()
      if x[0] != ".": 
        persona_names += [[x, x.replace(" ", "_")]]
        persona_names_set.add(x)

  persona_init_pos = []
  file_count = []
  for filepath in find_filenames(f"storage/{sim_code}/environment", ".json"):
    x = filepath.split("/")[-1].strip()
    if x[0] != ".": 
      file_count += [int(x.split(".")[0])]
  curr_json = f'storage/{sim_code}/environment/{str(max(file_count))}.json'
  with open(curr_json) as json_file:  
    persona_init_pos_dict = json.load(json_file)
    for key, val in persona_init_pos_dict.items(): 
      if key in persona_names_set: 
        persona_init_pos += [[key, val["x"], val["y"]]]

  os.remove(f_curr_step)

  context = {"sim_code": sim_code,
             "step": step, 
             "persona_names": persona_names,
             "persona_init_pos": persona_init_pos,
             "mode": "simulate"}
  template = "home/home.html"
  return render(request, template, context)


def replay(request, sim_code, step): 
  sim_code = sim_code
  step = int(step)

  persona_names = []
  persona_names_set = set()
  for i in find_filenames(f"storage/{sim_code}/personas", ""): 
    x = i.split("/")[-1].strip()
    if x[0] != ".": 
      persona_names += [[x, x.replace(" ", "_")]]
      persona_names_set.add(x)

  persona_init_pos = []
  file_count = []
  for i in find_filenames(f"storage/{sim_code}/environment", ".json"):
    x = i.split("/")[-1].strip()
    if x[0] != ".": 
      file_count += [int(x.split(".")[0])]
  curr_json = f'storage/{sim_code}/environment/{str(max(file_count))}.json'
  with open(curr_json) as json_file:  
    persona_init_pos_dict = json.load(json_file)
    for key, val in persona_init_pos_dict.items(): 
      if key in persona_names_set: 
        persona_init_pos += [[key, val["x"], val["y"]]]

  context = {"sim_code": sim_code,
             "step": step,
             "persona_names": persona_names,
             "persona_init_pos": persona_init_pos, 
             "mode": "replay"}
  template = "home/home.html"
  return render(request, template, context)


def replay_persona_state(request, sim_code, step, persona_name): 
  sim_code = sim_code
  step = int(step)

  persona_name_underscore = persona_name
  persona_name = " ".join(persona_name.split("_"))
  memory = f"storage/{sim_code}/personas/{persona_name}/bootstrap_memory"
  if not os.path.exists(memory): 
    memory = f"compressed_storage/{sim_code}/personas/{persona_name}/bootstrap_memory"

  with open(memory + "/scratch.json") as json_file:  
    scratch = json.load(json_file)

  with open(memory + "/spatial_memory.json") as json_file:  
    spatial = json.load(json_file)

  with open(memory + "/associative_memory/nodes.json") as json_file:  
    associative = json.load(json_file)

  a_mem_event = []
  a_mem_chat = []
  a_mem_thought = []

  for count in range(len(associative.keys()), 0, -1): 
    node_id = f"node_{str(count)}"
    node_details = associative[node_id]

    if node_details["type"] == "event":
      a_mem_event += [node_details]

    elif node_details["type"] == "chat":
      a_mem_chat += [node_details]

    elif node_details["type"] == "thought":
      a_mem_thought += [node_details]
  
  context = {"sim_code": sim_code,
             "step": step,
             "persona_name": persona_name, 
             "persona_name_underscore": persona_name_underscore, 
             "scratch": scratch,
             "spatial": spatial,
             "a_mem_event": a_mem_event,
             "a_mem_chat": a_mem_chat,
             "a_mem_thought": a_mem_thought}
  template = "persona_state/persona_state.html"
  return render(request, template, context)


def path_tester(request):
  context = {}
  template = "path_tester/path_tester.html"
  return render(request, template, context)


@csrf_exempt
def send_environment(request):
  """
  <FRONTEND to BACKEND> 
  This sends the frontend visual world information to the backend server. 
  It does this by writing the current environment representation to 
  "storage/environment/{step}.json" file. 
  ARGS:
    request: Django request
  RETURNS: 
    HttpResponse: string confirmation message. 
  """
  if request.method == 'POST':
    try:
      data = json.loads(request.body)
      step = data.get('step')
      sim_code = data.get('sim_code')
      environment = data.get('environment', {})

      # Save environment data
      sim_folder = f"storage/{sim_code}"
      if not os.path.exists(sim_folder):
        os.makedirs(sim_folder)

      # If using MQTT, require MQTT to be available
      if settings.USE_MQTT:
        if not mqtt_client or not mqtt_client.is_connected:
          raise RuntimeError("MQTT is enabled but client is not connected")
        mqtt_data = {
          "step": step,
          "environment": environment
        }
        mqtt_client.publish(f"reverie/{sim_code}/environment", mqtt_data)
        return JsonResponse({"status": "success"})
      else:
        env_file = f"{sim_folder}/environment/{step}.json"
        with open(env_file, 'w') as f:
          json.dump(environment, f, indent=2)
        return JsonResponse({"status": "success"})

    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)

  return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def get_movements(request):
  """
  <BACKEND to FRONTEND> 
  This sends the backend computation of the persona behavior to the frontend
  client.
  It does this by reading the new movement information from 
  "storage/movement/{step}.json" file.

  ARGS:
    request: Django request
  RETURNS: 
    HttpResponse
  """
  global movement_data
  
  if request.method == 'GET':
    try:
      data = json.loads(request.body)
      step = data.get('step')
      sim_code = data.get('sim_code')

      # If using MQTT, require MQTT to be available
      if settings.USE_MQTT:
        if not mqtt_client or not mqtt_client.is_connected:
          raise RuntimeError("MQTT is enabled but client is not connected")

        # Subscribe to movement topic if not already subscribed
        topic = f"reverie/{sim_code}/movement"
        if topic not in mqtt_client._handlers:
          mqtt_client.subscribe(topic, _handle_movement_update)

        # Check if we have movement data for this step
        if movement_data and movement_data.get("step") == step:
          return JsonResponse(movement_data)
        return JsonResponse({"<step>": step})

      else:
        # File-based communication if MQTT is disabled
        movement_file = f"storage/{sim_code}/movement/{step}.json"
        if os.path.exists(movement_file):
          with open(movement_file, 'r') as f:
            movement_data = json.load(f)
          return JsonResponse(movement_data)
        return JsonResponse({"<step>": step})

    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)

  return JsonResponse({"error": "Invalid request method"}, status=405)


def path_tester_update(request): 
  """
  Processing the path and saving it to path_tester_env.json temp storage for 
  conducting the path tester. 

  ARGS:
    request: Django request
  RETURNS: 
    HttpResponse: string confirmation message. 
  """
  data = json.loads(request.body)
  camera = data["camera"]

  with open(f"{fs_temp_storage}/path_tester_env.json", "w") as outfile:
    outfile.write(json.dumps(camera, indent=2))

  return HttpResponse("received")
