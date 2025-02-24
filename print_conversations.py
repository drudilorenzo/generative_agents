import glob
import os
import sys
import json

def get_unique_conversations(simulation_name):
    step_folder = "environment/frontend_server/storage"
    
    # Use glob to find all files that start with the simulation_name
    search_pattern = os.path.join(step_folder, f"{simulation_name}*/movement/*")
    filepaths = glob.glob(search_pattern)

    observed_conversations = set()
    file_contents = []

    # Iterate over all matching files
    for filepath in filepaths:
        with open(filepath, "r") as file:
            data = json.load(file)
            personas = data.get("persona", {})

            # Loop over all personas except one, since conversations are always
            # between two people
            for name in list(personas.keys())[:-1]:
                persona = personas[name]
                chat = persona.get("chat")

                if chat:
                    chat_string = str(chat)

                    # Add unique conversations
                    if chat_string not in observed_conversations:
                        observed_conversations.add(chat_string)
                        file_contents.append(data)
                        break

    return file_contents

def write_conversations_to_file(conversations, simulation_name):
   output_directory = "logs/conversations"
   if not os.path.exists(output_directory):
        os.makedirs(output_directory)
   output_filename = f"{simulation_name}_highlights.json"
   full_path = os.path.join(output_directory, output_filename);
   with open(full_path, "w") as file:
        for conversation in conversations:
            json.dump(conversation, file, indent=4)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the simulation name as a command line argument.")
        sys.exit(1)

    simulation_name = sys.argv[1]
    unique_conversations = get_unique_conversations(simulation_name)
    
    if unique_conversations:
        write_conversations_to_file(unique_conversations, simulation_name)
        print(f"Unique conversations written to {simulation_name}_highlights.txt")
    else:
        print("No unique conversations found.")