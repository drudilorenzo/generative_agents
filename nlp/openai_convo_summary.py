# This script is intended to be used to have openai summarize our agent
# conversations and determine for use the most relevent topics

##import libraries
import sys
from openai import OpenAI

client = OpenAI(api_key="Your API Key Here")


# Function declaration
def file_chuncking(file_path):
    chunk_size = 1024 * 1024
    chunks = []

    # Open the large file in read mode
    with open(file_path, "rb") as file:
        chunk = file.read(chunk_size)  # Read the first chunk

        while chunk:
            chunks.append(chunk)  # Add the chunk to the list
            chunk = file.read(chunk_size)  # Read the next chunk

    return chunks


def main():
    raw_file = sys.argv[1]

    pathtofile = f"convo-analysis/raw-text-convo/{raw_file}"

    file_chunks = file_chuncking(pathtofile)
    print(file_chunks[0])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """ 
            You are an expert natural language processing expert. You will be provided with the text data that is the conversation 
            between two generative agents. You will conduct a topic modeling analysis on the agent conversations. Then you will 
            report the analysis and a concise manner with detailed information.""",
            },
            {"role": "user", "content": f"{file_chunks[0]}"},
        ],
        temperature=0.7,
        max_tokens=4096,
        top_p=1,
    )
    print()
    print(response)


if __name__ == "__main__":
    main()
