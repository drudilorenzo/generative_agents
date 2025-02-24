import os
import json
import re
import sys

def get_unique_conversations(simulation_name):
    sim_folder = os.path.join("environment", "frontend_server", "storage")

    regex_name = re.compile(re.escape(simulation_name + '-'))
    for file_name in os.listdir(sim_folder):
        step=0
        output = []  
        if regex_name.search(file_name):
            step_folder = os.path.join(sim_folder, file_name, "movement")
            files=[filename for filename in os.listdir(step_folder)]
            files = sorted(files, key = lambda files:int(files[:-5]))
            for filename in files:
                filepath = os.path.join(step_folder, filename)
                output.append(f"Step {str(step)}:")
                try:
                    with open(filepath, "r") as file:
                        data = json.load(file)
                        for k, v in data.items():
                            output.append(k)
                            if k == 'persona':
                                for key, value in v.items():
                                    output.append(f'   {key}')
                                    for attribute, val in value.items():
                                        if attribute != 'chat' or (attribute == 'chat' and val is None):
                                            output.append(f'      {attribute}: {val}')
                                        else:
                                            output.append(f'      {attribute}:')
                                            for convo in val:
                                                output.append(f'         {convo[0]}: {convo[1]}')
                            else:
                                for key, value in v.items():
                                    output.append(f'   {key}: {value}')
                            output.append('\n')
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
                    continue
                step+=1

            output_filename = os.path.join(sim_folder, file_name, f"output_0-{file_name.split('-')[4]}.txt", )
            with open(output_filename, "w") as output_file:
                output_file.write('\n'.join(output))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the simulation name as a command line argument.")
        sys.exit(1)

    simulation_name = sys.argv[1]
    '''
    unique_conversations = get_unique_conversations(simulation_name)
    print(json.dumps(unique_conversations, indent=2))
    '''
    get_unique_conversations(simulation_name)
