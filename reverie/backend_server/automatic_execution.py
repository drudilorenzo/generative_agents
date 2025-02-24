#!/usr/bin/env python3

import gc
import os
import sys
import time
import shutil
import reverie
import argparse
import webbrowser
import subprocess
import traceback
from typing import Tuple, Union, Optional
from pathlib import Path
from datetime import datetime
from multiprocessing import Process
from openai_cost_logger import OpenAICostLoggerViz


def parse_args() -> Tuple[str, str, int, Union[bool, None], str, str, str]:
    """Parse bash arguments

    Returns:
        Tuple[str, str, int, bool]:
            - name of the forked simulation
            - the name of the new simulation
            - total steps to run (step = 10sec in the simulation)
            - open the simulator UI
    """
    parser = argparse.ArgumentParser(description='Reverie Server')
    parser.add_argument(
        '--origin',
        type=str,
        default="base_the_ville_isabella_maria_klaus",
        help='The name of the forked simulation'
    )
    parser.add_argument(
        '--target',
        type=str,
        default="test-simulation",
        help='The name of the new simulation'
    )
    parser.add_argument(
        '--steps',
        type=str,
        default="8640", # 24 hours
        help='Step to end after'
    )
    parser.add_argument(
        '--ui',
        type=str,
        default="True",
        choices=["True", "False", "None"],
        help='Open the simulator UI'
    )
    parser.add_argument(
        '--browser_path',
        type=str,
        default="/usr/bin/google-chrome %s",
        help='Browser path, default is /usr/bin/google-chrome %s'
    )
    parser.add_argument(
        '--port',
        type=str,
        default="8000",
        help='Port number for the frontend server'
    )
    parser.add_argument(
        '--load_history',
        type=str,
        required=False,
        help='Load agent history file'
    )
    origin = parser.parse_args().origin
    target = parser.parse_args().target
    steps = parser.parse_args().steps
    ui = parser.parse_args().ui
    ui = True if ui.lower() == "true" else False if ui.lower() == "false" else None
    browser_path = parser.parse_args().browser_path
    port = parser.parse_args().port
    history_file = parser.parse_args().load_history
    
    return origin, target, steps, ui, browser_path, port, history_file


def get_starting_step(exp_name: str) -> int:
    """Get the starting step of the experiment. 

    Returns:
        exp_name (str): The name of the experiment
    """
    current_step = 0
    experiments_directory = "../../environment/frontend_server/storage"
    full_path = Path(experiments_directory, exp_name, "movement")  
    if full_path.exists():
        files = os.listdir(full_path)
        steps = [int(os.path.splitext(filename)[0]) for filename in files]
        current_step = max(steps)
    return current_step


def start_web_tab(ui, browser_path: str, port: str) -> Optional[int]:
    """Open a new tab in the browser with the simulator home page
    
    Args:
        ui (bool): Open the simulator UI.
        browser_path (str): The path of the browser.
        port (str): The port number of the frontend server.
        
    Returns:
        Optional[int]: The process id of the web tab (only for headless chrome).
    """
    url = f"http://localhost:{port}/simulator_home"
    print("(Auto-Exec): Opening the simulator home page", flush=True)
    time.sleep(5)
    pid = None
    try:
        if ui:
            webbrowser.get(browser_path).open(url, new=2)
        else:
            command = [
                "google-chrome",
                "--headless=new",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--single-process",
                "--no-zygote",
                url
            ]

            process = subprocess.Popen(command)
            pid = process.pid
            print(f"(Auto-Exec): Web tab process started with pid {pid}", flush=True)
        return pid
    except Exception as e:
        print(e, flush=True)


def get_new_checkpoint(step: int, tot_steps: int, checkpoint_freq: int) -> int:
    """Get the current checkpoint from the checkpoint file

    Args:
        step (int): The current step.
        tot_steps (int): The total steps to run.
        checkpoint_freq (int): The frequency of the checkpoints.

    Returns:
        int: The new checkpoint.
    """
    new_checkpoint = step + checkpoint_freq
    if new_checkpoint > tot_steps:
        new_checkpoint = tot_steps
    return new_checkpoint


def save_checkpoint(rs, idx: int) -> Tuple[str, int, int]:
    """Save the checkpoint and return the data to start the new one.

    Args:
        rs (ReverieServer): The reverie server object.
        idx (int): The index of the checkpoint.
        th (Process): The process of the web tab.
    
    Returns:
        Tuple[str, int, int]: The name of the new experiment, the starting step and the index of the checkpoint.
    """
    target = rs.sim_code
    rs.open_server(input_command="fin")
    print(f"(Auto-Exec): Checkpoint saved: {target}", flush=True)    
    return target, get_starting_step(target), idx+1
    

def load_agent_history(rs, history_file: str) -> None:
    """Load agent history from a file.

    Args:
        rs (ReverieServer): The reverie server instance
        history_file (str): Path to the history file to load
    """
    print(f"(Auto-Exec): Loading agent history from {history_file}", flush=True)
    rs.open_server(input_command=f"call -- load history {history_file}")


if __name__ == '__main__':
    checkpoint_freq = 200 # 1 step = 10 sec
    max_stepbacks = 5
    curr_stepbacks = 0
    log_path = "cost-logs" # where the simulations' prints are stored
    idx = 0
    origin, target, tot_steps, ui, browser_path, port, history_file = parse_args()
    current_step = get_starting_step(origin)
    exp_name = target
    start_time = datetime.now()
    tot_steps = int(tot_steps)
    curr_checkpoint = get_new_checkpoint(current_step, tot_steps, checkpoint_freq)

    print("(Auto-Exec): STARTING THE EXPERIMENT", flush=True)
    print(f"(Auto-Exec): Origin: {origin}", flush=True)
    print(f"(Auto-Exec): Target: {target}", flush=True)
    print(f"(Auto-Exec): Total steps: {tot_steps}", flush=True)
    print(f"(Auto-Exec): Checkpoint Freq: {checkpoint_freq}", flush=True)

    while current_step < tot_steps:
        try:
            steps_to_run = curr_checkpoint - current_step
            target = f"{exp_name}-s-{idx}-{current_step}-{curr_checkpoint}"
            print(f"(Auto-Exec): STAGE {idx}", flush=True)
            print(f"(Auto-Exec): Running experiment '{exp_name}' from step '{current_step}' to '{curr_checkpoint}'", flush=True)
            rs = reverie.ReverieServer(origin, target)

            # Load agent history if provided
            if history_file and current_step == 0:
                load_agent_history(rs, history_file)

            th, pid = None, None
            # Headless chrome doesn't need a thread since it create a dedicated thread by itself
            if ui == True:
                th = Process(target=start_web_tab, args=(ui, browser_path, port))
                th.start()
                rs.open_server(input_command=f"run {steps_to_run}")
            elif ui == False:
                pid = start_web_tab(ui, browser_path, port)
                rs.open_server(input_command=f"run {steps_to_run}")
            elif ui is None:
                rs.open_server(input_command=f"headless {steps_to_run}")
        except KeyboardInterrupt:
            print("(Auto-Exec): KeyboardInterrupt: Stopping the experiment.", flush=True)
            sys.exit(0)
        except Exception as e:
            traceback.print_exc()
            step = e.args[1]

            if len(e.args) > 2 and e.args[2] == "stepback":
                curr_stepbacks += 1
                if curr_stepbacks > max_stepbacks:
                    print("(Auto-Exec): Maximum consecutive stepbacks reached. Aborting the experiment.", flush=True)
                    if step <= 0:
                      # Remove the experiment folder if no steps were run
                      shutil.rmtree(f"../../environment/frontend_server/storage/{target}") 
                    break
            else:
                curr_stepbacks = 0

            if step > 0:
                origin, current_step, idx = save_checkpoint(rs, idx)

            print(f"(Auto-Exec): Error at step {current_step}", flush=True)
            print(f"(Auto-Exec): Exception {e.args[0]}", flush=True)
        else:
            origin, current_step, idx = save_checkpoint(rs, idx)
            curr_checkpoint = get_new_checkpoint(current_step, tot_steps, checkpoint_freq)
        finally:
            time.sleep(10) # Wait for the server to finish and then kill the process
            if th and th.is_alive():
                th.kill()
                th.join()
                th.close()
                gc.collect()
        
            if pid:
                os.system(f"kill -9 {pid}")
                print(f"(Auto-Exec): Killed web tab process with pid {pid}", flush=True)
                pid = None

    print(f"(Auto-Exec): EXPERIMENT FINISHED: {exp_name}")
    OpenAICostLoggerViz.print_experiment_cost(experiment=exp_name, path=log_path)
    OpenAICostLoggerViz.print_total_cost(path=log_path)
    print(f"(Auto-Exec): Execution time: {datetime.now() - start_time}")
    sys.exit(0)