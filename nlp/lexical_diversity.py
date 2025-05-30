from nltk.tokenize import word_tokenize


def lexical_diversity(text):
    return len(set(text)) / len(text)


file = "test.txt"

with open(file, "r") as f:
    # Tokenize and remove punctuation
    content = f.read()
    tokens = word_tokenize(content)
    tokens = [word.lower() for word in tokens if word.isalpha()]

    # Calculate lexical diversity
    lexical_diversity_score = lexical_diversity(tokens)
    print(f"Lexical Diversity: {lexical_diversity_score}")
