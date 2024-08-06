"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""
import time 
import json
from pathlib import Path
from openai import AzureOpenAI, OpenAI

from utils import *
from openai_cost_logger import DEFAULT_LOG_PATH
from persona.prompt_template.openai_logger_singleton import OpenAICostLogger_Singleton

config_path = Path("../../llm_config.json")
with open(config_path, "r") as f:
    openai_config = json.load(f) 

def setup_client(type: str, config: dict):
  """Setup the OpenAI client.

  Args:
      type (str): the type of client. Either "azure" or "openai".
      config (dict): the configuration for the client.

  Raises:
      ValueError: if the client is invalid.

  Returns:
      The client object created, either AzureOpenAI or OpenAI.
  """
  if type == "azure":
    client = AzureOpenAI(
        azure_endpoint=config["endpoint"],
        api_key=config["key"],
        api_version=config["api-version"],
    )
  elif type == "openai":
    client = OpenAI(
        api_key=config["key"],
    )
  elif type == "ollama":
    # ollama can use the OpenAI interface
    client = OpenAI(
        api_key=config["key"],
        base_url=config["base_url"]
    )

  else:
    raise ValueError("Invalid client")
  return client

if openai_config["client"] == "azure":
  client = setup_client("azure", {
      "endpoint": openai_config["model-endpoint"],
      "key": openai_config["model-key"],
      "api-version": openai_config["model-api-version"],
  })
elif openai_config["client"] == "openai":
  client = setup_client("openai", { "key": openai_config["model-key"] })
elif openai_config["client"] == "ollama":
  client = setup_client("ollama", { "key": openai_config["model-key"],
                                               "base_url": openai_config["base_url"] })
else:
  raise Exception("No valid client selected!")

if openai_config["embeddings-client"] == "azure":  
  embeddings_client = setup_client("azure", {
      "endpoint": openai_config["embeddings-endpoint"],
      "key": openai_config["embeddings-key"],
      "api-version": openai_config["embeddings-api-version"],
  })
elif openai_config["embeddings-client"] == "openai":
  embeddings_client = setup_client("openai",{ "key": openai_config["embeddings-key"] })
elif openai_config["embeddings-client"] == "ollama":
  embeddings_client = setup_client("ollama", { "key": openai_config["embeddings-key"],
                                               "base_url": openai_config["base_url"] })
else:
  raise ValueError("Invalid embeddings client")


cost_logger = OpenAICostLogger_Singleton(
  experiment_name = openai_config["experiment-name"],
  log_folder = DEFAULT_LOG_PATH,
  cost_upperbound = openai_config["cost-upperbound"]
)


def temp_sleep(seconds=0.1):
  time.sleep(seconds)


def ChatGPT_single_request(prompt): 
  temp_sleep()
  completion = client.chat.completions.create(
    model=openai_config["model"],
    messages=[{"role": "user", "content": prompt}]
  )
  cost_logger.update_cost(completion, input_cost=openai_config["model-costs"]["input"], output_cost=openai_config["model-costs"]["output"])
  return completion.choices[0].message.content


def ChatGPT_request(prompt): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  # temp_sleep()
  try: 
    completion = client.chat.completions.create(
    model=openai_config["model"],
    messages=[{"role": "user", "content": prompt}]
    )
    cost_logger.update_cost(completion, input_cost=openai_config["model-costs"]["input"], output_cost=openai_config["model-costs"]["output"])
    return completion.choices[0].message.content
  
  except Exception as e: 
    print(f"Error: {e}")
    return "ChatGPT ERROR"


# this function is frustratingly similar to safe_generate_response
def ChatGPT_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=5,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "So for example do not output 5 output {'output': 5}"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  for i in range(repeat): 
    if verbose: 
      print ("---- repeat count: \n", i)
      print("---- prompt: ", prompt)
    curr_gpt_response = ChatGPT_request(prompt).strip()
    if verbose: 
      print("---- curr_gpt_response: ", curr_gpt_response)
    try:
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]
    except Exception as e:
      if verbose:
        print("ERROR func_clean_up: ", e)
      continue

    if verbose: 
      print("---- func_validate: ", func_validate(curr_gpt_response))
      try:
          print("----  func_clean_up: ", func_clean_up(curr_gpt_response))
      except Exception as e:
          print("ERROR func_clean_up: ", e)
      print ("~~~~")

    if func_validate(curr_gpt_response, prompt=prompt): 
      return func_clean_up(curr_gpt_response, prompt=prompt)


  if EXCEPT_ON_FAILSAFE:
    raise Exception("Too many retries and failsafes are disabled!")
  else:
    return fail_safe_response

def GPT_request(prompt, gpt_parameter): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  temp_sleep()
  try: 
    # for the llama3 model system doesn't give great results
    # and assistant is much better
    messages = [{
      "role": "user", "content": prompt
    }]
    response = client.chat.completions.create(
                model=gpt_parameter["engine"],
                messages=messages,
                temperature=gpt_parameter["temperature"],
                max_tokens=gpt_parameter["max_tokens"],
                top_p=gpt_parameter["top_p"],
                frequency_penalty=gpt_parameter["frequency_penalty"],
                presence_penalty=gpt_parameter["presence_penalty"],
                stream=gpt_parameter["stream"],
                stop=gpt_parameter["stop"],)
    cost_logger.update_cost(response=response, input_cost=openai_config["model-costs"]["input"], output_cost=openai_config["model-costs"]["output"])
    return response.choices[0].message.content
  except Exception as e:
    print(f"Error: {e}")
    return "TOKEN LIMIT EXCEEDED"


def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the GPT3 server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
  """
  if debug:
    print("curr_input: ", curr_input)
    print("prompt_lib_file: ", prompt_lib_file)
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r")
  prompt = f.read()
  f.close()
  if debug:
    print("---- prompt template inputs")
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
    if debug:
      print(f"        !<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()

# this function is frustratingly similar to CHATGPT_safe_generate_response
def safe_generate_response(prompt, 
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           prompt_input=[],
                           prompt_template="",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  if debug:
    verbose = True

  for i in range(repeat): 

    if verbose: 
      print("------- BEGIN SAFE GENERATE --------")
      print ("---- repeat count: ", i)
      for j, prompt_j in enumerate(prompt_input):
        print("---- prompt_input_{}".format(j), prompt_j)
      print("---- prompt: ", prompt)
      print("---- prompt_template: ", prompt_template)
      print("---- gpt_parameter: ", gpt_parameter)

    curr_gpt_response = GPT_request(prompt, gpt_parameter)

    if verbose: 
      print("---- curr_gpt_response: ", curr_gpt_response)

    try: 
      response_cleanup = func_clean_up(curr_gpt_response, prompt=prompt)
    except Exception as e:
      if verbose:
        print("----  func_clean_up:  ERROR", e)
        print("---- func_validate: ", False)
        print(f"------- END TRIAL {i} --------")
      continue

    try: 
      response_valid = func_validate(curr_gpt_response, prompt=prompt)
    except Exception as e:
      if verbose:
        print("----  func_clean_up: ", response_cleanup)
        print("---- func_validate: ERROR", e)
        print(f"------- END TRIAL {i} --------")
      continue

    if verbose:
      print("----  func_clean_up: ", response_cleanup)
      print("---- func_validate: ", response_valid)
      print(f"------- END TRIAL {i} --------")
    if response_valid:
      print("------- END SAFE GENERATE --------")
      return response_cleanup
  
  # behaviour if all retries are used up
  if EXCEPT_ON_FAILSAFE:
    raise Exception("Too many retries and failsafes are disabled!")
  else:
    print("ERROR fail to succesfully retrieve response")
    print("ERROR using fail_safe: ", fail_safe_response)
    print("------- END SAFE GENERATE --------")
    return fail_safe_response

def get_embedding(text, model=openai_config["embeddings"]):
  text = text.replace("\n", " ")
  if not text: 
    text = "this is blank"

  # ollama does not support the client interface for embeddings 
  # so this needs to be managed separately 
  if openai_config["client"] == "ollama":
    import ollama
    return ollama.embeddings(model=model,prompt=text)['embedding']
  else:
    response = embeddings_client.embeddings.create(input=[text], model=model)
    cost_logger.update_cost(response=response, input_cost=openai_config["embeddings-costs"]["input"], output_cost=openai_config["embeddings-costs"]["output"])
    return response.data[0].embedding



if __name__ == '__main__':
  gpt_parameter = {"engine": openai_config["model"], "max_tokens": 50, 
                   "temperature": 0, "top_p": 1, "stream": False,
                   "frequency_penalty": 0, "presence_penalty": 0, 
                   "stop": ['"']}
  curr_input = ["driving to a friend's house"]
  prompt_lib_file = "prompt_template/test_prompt_July5.txt"
  prompt = generate_prompt(curr_input, prompt_lib_file)

  def __func_validate(gpt_response): 
    if len(gpt_response.strip()) <= 1:
      return False
    if len(gpt_response.strip().split(" ")) > 1: 
      return False
    return True
  def __func_clean_up(gpt_response):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  output = safe_generate_response(prompt, 
                                 gpt_parameter,
                                 5,
                                 "rest",
                                 __func_validate,
                                 __func_clean_up,
                                 True)

  print (output)
