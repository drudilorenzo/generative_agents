#This script is intended to analyze agent conversations 

#importing modules
import json
import sys

# Function to analyze conversations and search for specific keywords
def analyze_convo(json_file, json_data, keywords):
    non_rep_convos = set()
    # Iterate through each entry in the JSON data
    for entry in json_data:
        # Check each persona's conversation if available
        for persona, details in entry['persona'].items():
            if 'chat' in details and details['chat']:
                for conversation in details['chat']:
                    # Check if any of the keywords are in the conversation
                    for keyword in keywords:
                        if conversation[1] in non_rep_convos: 
                            continue 
                        if keyword in conversation[1]:
                            non_rep_convos.add(f"Keyword '{keyword}' found in conversation of {conversation[0]}: {conversation}")
                            keywords[keyword] += 1

    with open(f"convo-analysis/key-words/{json_file}.txt", "w") as newfile:
        newfile.write("Keywords in Agent Conversations:\n")
        for element in non_rep_convos:
            newfile.write(f"{element}\n")
        newfile.write("\n")
        newfile.write(f"Keyword Count:\n")
        for key in keywords.keys():
            newfile.write(f"{key}: {keywords[key]}\n")

def main():
    try:
        # Load the JSON data
        json_file = sys.argv[1]
        step_file = f"convo-analysis/JSON/{json_file}"

        with open(step_file, "r") as file:
            json_data = json.load(file)

        # Define the keywords to search for and keeping a number count
        keywords = {'hiding': 0 ,'hide' : 0, 'trick': 0, 'tricky': 0, 'search': 0, 'find': 0, 'found you' : 0, 'found': 0} 

        # Analyze the conversations
        analyze_convo(json_file, json_data, keywords)

    except IndexError:
        print("Error: No file name provided.")
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON file.")
        print(json_file)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
