import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
import os
import json

MODEL_DIR = "models/relevance"
TRAINING_DATA = "models/relevance/train.jsonl"

def get_nlp():
    if os.path.isdir(MODEL_DIR):
        return spacy.load(MODEL_DIR)
    nlp = spacy.blank("en")
    textcat = nlp.add_pipe("textcat")
    # two labels: RELEVANT, IRRELEVANT
    textcat.add_label("RELEVANT")
    textcat.add_label("IRRELEVANT")
    return nlp

def train_textcat(nlp, n_iter=10):
    # load existing examples
    examples = []
    with open(TRAINING_DATA, "r") as f:
        for line in f:
            data = json.loads(line)
            examples.append(Example.from_dict(nlp.make_doc(data["text"]), data["cats"]))

    optimizer = nlp.begin_training()
    for i in range(n_iter):
        random.shuffle(examples)
        batches = minibatch(examples, size=compounding(4.0, 32.0, 1.5))
        for batch in batches:
            nlp.update(batch, sgd=optimizer)
    # save
    os.makedirs(MODEL_DIR, exist_ok=True)
    nlp.to_disk(MODEL_DIR)

def predict_relevance(nlp, texts):
    textcat = nlp.get_pipe("textcat")
    docs = list(nlp.pipe(texts))
    preds = []
    for doc in docs:
        scores = doc.cats
        label = max(scores, key=scores.get)
        preds.append((label, scores[label]))
    return preds

def add_feedback(text, is_relevant: bool):
    # append to train.jsonl
    cats = {"RELEVANT": is_relevant, "IRRELEVANT": not is_relevant}
    with open(TRAINING_DATA, "a") as f:
        f.write(json.dumps({"text": text, "cats": cats}) + "\n")