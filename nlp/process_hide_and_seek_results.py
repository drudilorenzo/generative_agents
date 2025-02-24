import os
import json
import sys


def read_simulation_files(simulation_name):
    plugin_output_path = f"environment/frontend_server/storage/{simulation_name}/plugins/hide-and-seek/output"

    # Check if the directory exists
    if not os.path.isdir(plugin_output_path):
        print(f"The directory {plugin_output_path} does not exist.")
        return

    files = os.listdir(plugin_output_path)
    # Sort by number
    files.sort(key=lambda x: int(x.split("-")[0]))

    # Iterate over all files in the directory
    for filename in files:
        # Check if the file is a JSON file
        if filename.endswith(".json"):
            # print(filename)

            # Construct the full file path
            file_path = os.path.join(plugin_output_path, filename)

            # Open the file and load the JSON data
            with open(file_path, "r") as file:
                data = json.load(file)

                game_ended_value = data[0]["Did a game of hide-and-seek just end?"]
                # print(type(game_ended_value), game_ended_value)

                game_ended = (
                    game_ended_value
                    if type(game_ended_value) == bool
                    else game_ended_value.lower() == "true"
                )

                if game_ended:
                    print(filename)
                    print("game_ended:", game_ended)
                    print(json.dumps(data, indent=2))
                    print()


# Check if a command-line argument was provided
if len(sys.argv) < 2:
    print("Please provide a simulation name as a command-line argument.")
else:
    # Call the function with the simulation name as argument
    read_simulation_files(sys.argv[1])
