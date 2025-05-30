# Simulacra Utilities

This directory contains utility scripts for managing and analyzing simulation data.

## Scripts

### `print_conversations.py`
A tool for extracting and saving unique conversations from a simulation. It identifies distinct conversations between personas and saves them to a JSON file in the `logs/conversations` directory.

### `print_all_sim.py`
A utility that generates detailed output files for a given simulation, including all steps, personas, and their attributes. It creates a comprehensive text file containing the complete simulation data.

### `monitor_simulation.py`
A real-time monitoring tool for headless simulations (simulations running without the UI). It watches the current simulation's movement files and displays updates as they occur, automatically refreshing to show the latest simulation state.

### `clean_sim_folders.py`
A utility for cleaning up simulation folders by identifying and removing older versions of the same simulation. It helps maintain disk space by keeping only the latest version of each simulation run.

## Usage

Each script can be run from the command line. For example:

```bash
python print_conversations.py simulation_name
python print_all_sim.py simulation_name
python monitor_simulation.py
python clean_sim_folders.py [--dir directory_path] [--execute] [--automatic]
```

## Interactive Cost Visualization

### `cost_viz.ipynb`
An interactive Jupyter notebook for visualizing the cost that a simulation acrues by accessing a paid LLM service like OpenAI or Azure.
