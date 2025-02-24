# This script is intended to scape agent conversations only

# importing modules
import json
import sys


# Function to analyze conversations and search for specific keywords
def raw_text_scrape(json_data, json_file):
    raw_data = []
    # Iterate through each entry in the JSON data
    for entry in json_data:
        # Check each persona's conversation if available
        for persona, details in entry["persona"].items():
            if "chat" in details and details["chat"]:
                for conversation in details["chat"]:
                    raw_data.append(conversation[1])
                    # print(f"{conversation[1]}\n")

    with open(f"convo-analysis/raw-text-convo/{json_file[:-5]}.txt", "w") as newfile:
        for i in range(len(raw_data)):
            newfile.write(f"{raw_data[i]}\n")


def main():
    try:
        # Load the JSON data
        json_file = sys.argv[1]
        step_file = f"convo-analysis/JSON/{json_file}"

        with open(step_file, "r") as file:
            json_data = json.load(file)

        # Analyze the conversations
        raw_text_scrape(json_data, json_file)

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
