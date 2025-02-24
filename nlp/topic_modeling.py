# This script is intended to be used for test on the agent conversations
# with regard to topic modeling

# importing libraries
import sys
import nltk
import spacy
import gensim
import gensim.corpora as corpora
from nltk.corpus import stopwords
from gensim.models.ldamodel import LdaModel


# Prepare Data set
def load_data(file):
    data = []
    with open(file, "r") as file:
        for line in file:
            processed_line = line.strip()
            data.append(processed_line)

    return data


# Tokenize, remove stopwords, and lemmatize
def preprocess(text):
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in stop_words:
            result.append(token)
    return [
        token.lemma_
        for token in nlp(" ".join(result))
        if token.pos_ in ["NOUN", "ADJ", "VERB", "ADV"]
    ]


# try:
# Prepare dataset
raw_text_file = sys.argv[1]
step_file = f"convo-analysis/raw-text-convo/{raw_text_file}"
dataset = load_data(step_file)

# Ensure you have the stopwords dataset downloaded
nltk.download("stopwords")
# Load spaCy model for lemmatization
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

# Extend stopwords list if necessary
stop_words = stopwords.words("english")
stop_words.extend(["from", "subject", "re", "edu", "use"])


processed_data = [preprocess(dataset[i]) for i in range(len(dataset))]
# Create Dictionary
id2word = corpora.Dictionary(processed_data)

# Create Corpus
texts = processed_data

# Term Document Frequency
corpus = [id2word.doc2bow(text) for text in texts]
# Number of Topics
num_topics = 10

# Build LDA model
lda_model = LdaModel(
    corpus=corpus,
    id2word=id2word,
    num_topics=num_topics,
    random_state=100,
    update_every=1,
    chunksize=100,
    passes=10,
    alpha="auto",
    per_word_topics=True,
)

# Get the topics and their weights
topics = lda_model.print_topics(num_words=10)

# Open the file in write mode
with open(
    f"convo-analysis/topic-modeling-output/{raw_text_file[:-4]}.txt", "w"
) as newfile:
    newfile.write("Topic Modeling Analysis:\n")
    for topic_number, topic_words in topics:
        # Write each topic as a new line
        newfile.write(f"Topic {topic_number}: {topic_words}\n")


# except IndexError:
#     print("Error: No file name provided.")
# except FileNotFoundError:
#     print(f"Error: File '{raw_text_file}' not found.")
# except Exception as e:
#     print(f"An unexpected error occurred: {e}")
