

# Generative Agents Collaboratively Mission-Planning 

<p align="center" width="100%">
<img src="cover.png" alt="Smallville" style="width: 80%; min-width: 300px; display: block; margin: auto;">
</p>

This repository is an evolution of the repository based on the paper "[Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)."

_______________________________________
## Index:
1. [Setup](#setting-up-the-environment)
2. [Execution](#running-a-simulation)
3. [Cost-Tracking](#cost-tracking)
4. [Customizing the Map](#customizing-the-map)
_______________________________________

## Setting Up The Environment

### Step 1. Conda Env

Note: If you change the environment name from `simulacra`, you'll need to update the name in the upcoming bash scripts as well.
```bash
    conda create -n simulacra python=3.9.12 pip
    conda activate simulacra
    pip install -r requirements.txt
```


### Step 2. OpenAI Config

Create a file called `openai_config.json` in the root directory.

OpenAI example:
```json
{
    "client": "openai", 
    "model": "gpt-4o-mini",
    "model-key": "<API-KEY>",
    "model-costs": {
        "input":  0.5,
        "output": 1.5
    },
    "embeddings-client": "openai",
    "embeddings": "text-embedding-3-small",
    "embeddings-key": "<API-KEY>",
    "embeddings-costs": {
        "input": 0.02,
        "output": 0.0
    },
    "experiment-name": "simulacra-test",
    "cost-upperbound": 10
}
```

Azure example:
```json
{
    "client": "azure", 
    "model": "gpt-4o-mini",
    "model-key": "<API-KEY>",
    "model-endpoint": "<MODEL-ENDPOINT>",
    "model-api-version": "<API-VERSION>",
    "model-costs": {
        "input":  0.5,
        "output": 1.5
    },
    "embeddings-client": "azure",
    "embeddings": "text-embedding-3-small",
    "embeddings-key": "<API-KEY>",
    "embeddings-endpoint": "<EMBEDDING-MODEL-ENDPOINT>",
    "embeddings-api-version": "<API-VERSION>",
    "embeddings-costs": {
        "input": 0.02,
        "output": 0.0
    },
    "experiment-name": "simulacra-test",
    "cost-upperbound": 10
}
```

Feel free to change and test also other models (and change accordingly the input and output costs). Note that this repo uses OpenAI's Structured Outputs feature, which is currently only available for certain models, like the GPT-4o series. Check the OpenAI docs for more info. \
The generation and the embedding models are configured separately to be able to use different clients.\
Change also the `cost-upperbound` according to your needs (the cost computation is done using "[openai-cost-logger](https://github.com/drudilorenzo/openai-cost-logger)" and the costs are specified per million tokens).

Next, you will (for now) also need to set up the `utils.py` file as described in the [original repo's README](README_origin.md). After creating the file as described there, add these lines to it and change them as necessary:

```
use_openai = True
# If you're not using OpenAI, define api_model
api_model = ""
```

## Running a simulation

> All of the following scripts accept two optional arguments to customize the conda setup:
> - `--conda_path`: Path to your conda activate script (default: `/home/${USER}/anaconda3/bin/activate`)
> - `--env_name`: Name of the conda environment to use (default: `simulacra`)
>
> Example with custom conda setup:
> ```bash
> ./run_frontend.sh --conda_path /path/to/conda/activate --env_name my_env [other args...]
> ```

### Step 1. Starting the Environment Server
If you're running the backend in headless mode (see below), you can skip this step.

```bash
    ./run_frontend.sh [--conda_path PATH] [--env_name ENV] [PORT-NUMBER]
```
 >Note: omit the port number to use the default 8000.

### Step 2. Starting the Simulation Server

#### Option 1: Running the server manually
```bash
    ./run_backend.sh [--conda_path PATH] [--env_name ENV] <ORIGIN> <TARGET>
```
Example:
```bash
    ./run_backend.sh base_the_ville_isabella_maria_klaus simulation-test
```

See the [original README](README_origin.md) for commands to pass to the server when running it manually. In addition to the commands listed there, you can also use the command `headless` in place of `run` (i.e. `headless 360` rather than `run 360`) to run in headless mode.

#### Option 2. Automatic Execution
The following script offer a range of enhanced features:
- **Automatic Saving**: The simulation automatically saves progress every 200 steps, ensuring you never lose data.
- **Error Recovery**: In the event of an error, the simulation automatically resumes by stepping back and restarting from the last successful point. This is crucial as the model relies on formatted answers, which can sometimes cause exceptions.
- **Automatic Tab Opening**: A new browser tab will automatically open when necessary.
- **Headless Mode**: The scripts support running simulations in headless mode, enabling execution on a server without a UI.
- **Configurable Port Number**: You can configure the port number as needed.

For more details, refer to: [run_backend_automatic.sh](run_backend_automatic.sh) and [automatic_execution.py](reverie/backend_server/automatic_execution.py).
```bash
    ./run_backend_automatic.sh [--conda_path <PATH>] [--env_name <ENV>] -o <ORIGIN> -t <TARGET> -s <STEP> --ui <True|None|False> -p <PORT> --browser_path <BROWSER-PATH> [--load_history <HISTORY-FILE>]
```

Arguments taken by `run_backend_automatic.sh`:
- `--conda_path`: (Optional) Path to your conda activate script
- `--env_name`: (Optional) Name of the conda environment to use
- `-o <ORIGIN>`: The name of an existing simulation to use as the base for the new simulation.
- `-t <TARGET>`: The new simulation name (Note: you cannot have multiple simulations of the same name).
- `-s <STEP>`: The step number to end on (NOT necessarily the number of steps to run for!).
- `--ui <True|None|False>`: Whether to run the UI or run the simulation headless (no UI). There are two different headless modes: "None" runs in pure headless mode (no browser needed), whereas "False" runs in Chrome's builtin headless mode (needs [headless-chrome](https://developer.chrome.com/blog/headless-chrome) installed). Prefer "None" over "False" in normal cases.
- `-p <PORT>`: The port to run the simulation on.
- `--browser_path <BROWSER-PATH>`: The path to the UI in the browser.
- `--load_history <HISTORY-FILE>`: (Optional) Load an agent history file. Start path with "./" to make it relative to the project root, otherwise it's interpreted as relative to the maze assets folder (`environment/frontend_server/static_dirs/assets/`).

Example:
```bash
    ./run_backend_automatic.sh -o base_the_ville_isabella_maria_klaus -t test_1 -s 4 --ui None
```

### Endpoint list
- [http://localhost:8000/](http://localhost:8000/) - check if the server is running
- [http://localhost:8000/simulator_home](http://localhost:8000/simulator_home) - watch the live simulation
- `http://localhost:8000/replay/<simulation-name>/<starting-time-step>` - replay a simulation

For a more detailed explanation see the [original readme](README_origin.md).


## Cost Tracking

For the cost tracking is used the package "[openai-cost-logger](https://github.com/drudilorenzo/openai-cost-logger)". Given the possible high cost of a simulation,  you can set a cost upperbound in the config file to be able to raise an exception and stop the execution when it is reached.

See all the details of your expenses using the notebook "[cost_viz.ipynb](utils/cost_viz.ipynb)."

## Cost Assessment

### 1. base_the_ville_isabella_maria_klaus

- **Model**: "gpt-3.5-turbo-0125"
- **Embeddings**: "text-embedding-3-small"
- **N. Agents**: 3
- **Steps**: ~5000
- **Final Cost**: ~0.31 USD

### 2. base_the_ville_n25

- See the simulation saved: [skip-morning-s-14](environment/frontend_server/storage/skip-morning-s-14)
- **Model**: "gpt-3.5-turbo-0125"
- **Embeddings**: "text-embedding-3-small"
- **N. Agents**: 25
- **Steps**: ~3000 (until ~8 a.m.)
- **Final Cost**: ~1.3 USD

### 3. base_the_ville_n25

- **Model**: "gpt-3.5-turbo-0125"
- **Embeddings**: "text-embedding-3-small"
- **N. Agents**: 25
- **Steps**: ~8650 (full day)
- **Final Cost**: ~18.5 USD

## Customizing the Map

The default simulation map, "The Ville", is a small town with locations such as a college, apartments, a cafe, a market, etc. The full list of locations and objects in this map are contained in the following files: [`sector_blocks.csv`](environment/frontend_server/static_dirs/assets/the_ville/matrix/special_blocks/sector_blocks.csv), [`arena_blocks.csv`](environment/frontend_server/static_dirs/assets/the_ville/matrix/special_blocks/arena_blocks.csv), and [`game_object_blocks.csv`](environment/frontend_server/static_dirs/assets/the_ville/matrix/special_blocks/game_object_blocks.csv). These are organized in a rough hierarchy: sector blocks roughly define buildings, arena blocks define rooms in buildings, and game object blocks define objects or areas in rooms.

To fully overhaul the map for your own customized simulation, you'd probably need to use the Tiled map editor as described in the [original repo's README](README_origin.md). This repo has added a shortcut method of customizing the map: renaming locations and objects that already exist in the Ville map.

To use this feature, add a `block_remaps` property to your simulation's `meta.json` file. Here's an example of remapping the supply store to be a fire station instead:

```json
{
  "fork_sim_code": "base_the_ville_isabella_maria_klaus",
  "start_date": "February 13, 2023",
  "curr_time": "February 13, 2023, 00:00:00",
  "sec_per_step": 10,
  "maze_name": "the_ville",
  "persona_names": [
    "Isabella Rodriguez",
    "Maria Lopez",
    "Klaus Mueller"
  ],
  "step": 0,
  "block_remaps": {
    "sector": {
      "Harvey Oak Supply Store": "Fire station"
    },
    "arena": {
      "supply store": "fire station"
    },
    "game_object": {
      "supply store product shelf": "fire truck",
      "supply store counter": "common area",
      "behind the supply store counter": "bunks"
    }
  }
}
```

When using this feature, reference the existing blocks in the blocks CSVs listed above. **Make sure to spell and case everything exactly as they are in those files!**

After remapping locations and objects in `meta.json`, you'll also need to rename them in each agent's `spatial_memory.json` file too, if they're referenced. This file defines what locations the agent is already aware of when the simulation starts. For instance, here's a link to Isabella's spatial memory file for the `base_the_ville_isabella_maria_klaus` simulation: [`spatial_memory.json`](environment/frontend_server/storage/base_the_ville_isabella_maria_klaus/personas/Isabella%20Rodriguez/bootstrap_memory/spatial_memory.json). Also, if a particular location is referenced in an agent's `scratch.json`, you'll need to update that too: [`scratch.json`](environment/frontend_server/storage/base_the_ville_isabella_maria_klaus/personas/Isabella%20Rodriguez/bootstrap_memory/scratch.json).
