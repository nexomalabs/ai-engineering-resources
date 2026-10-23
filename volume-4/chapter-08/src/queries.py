"""Step 2: the 50-query dataset, in the order the benchmark runs it."""

UNIQUE = [
    "What is gradient descent?",
    "How does dropout prevent overfitting?",
    "What is the difference between precision and recall?",
    "How does a transformer use attention?",
    "What is a learning rate schedule?",
    "Why do we normalize input features?",
    "What is transfer learning?",
    "How does k-means clustering work?",
    "What is the vanishing gradient problem?",
    "What does an embedding represent?",
]

# Same meaning. Some reuse the original's key words; some reword it.
PARAPHRASES = [
    "Can you explain gradient descent?",
    "How does dropout help prevent overfitting?",
    "Explain precision versus recall.",
    "How do transformers use attention?",
    "What's a learning-rate schedule?",
    "Why should input features be normalized?",
    "Explain transfer learning in simple terms.",
    "How does the k-means algorithm group data points?",
    "Why do gradients vanish in deep networks?",
    "What do embeddings represent?",
]

# Exact repetitions, with the case and spacing changes the exact key normalizes away.
REPEATS = [
    "What is gradient descent?",
    "how does dropout prevent overfitting?",
    "What is the difference between precision and recall?",
    "  How does a transformer use attention?  ",
    "What is a learning rate schedule?",
    "WHY DO WE NORMALIZE INPUT FEATURES?",
    "What is transfer learning?",
    "How does k-means clustering work?",
    "What is the vanishing gradient problem?",
    "What does an embedding represent?",
]

UNRELATED = [
    "What is the capital of Canada?",
    "How do I make sourdough bread?",
    "Who wrote Pride and Prejudice?",
    "What causes ocean tides?",
    "How many bones are in the human body?",
    "What is the boiling point of water at sea level?",
    "How do vaccines train the immune system?",
    "What is a Roth IRA?",
    "How do solar panels generate electricity?",
    "What is the tallest building in the world?",
    "How do I change a flat tire?",
    "What is photosynthesis?",
    "Who painted the Mona Lisa?",
    "How does a mortgage work?",
    "What is the speed of sound?",
    "How do bees make honey?",
    "What is inflation?",
    "How do I brew pour-over coffee?",
    "What is the largest desert on Earth?",
    "How does GPS determine location?",
]

QUERIES = UNIQUE + PARAPHRASES + REPEATS + UNRELATED
assert len(QUERIES) == 50
