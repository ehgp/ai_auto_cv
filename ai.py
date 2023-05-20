# Web Scraping
import os

# Natural Language Processing
import nltk

# Machine Learning
import numpy as np
import pandas as pd
import requests
import scrapy
import spacy
import tensorflow as tf
from bs4 import BeautifulSoup

# Misc
from dotenv import load_dotenv
from gensim.models import Word2Vec
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

# Database
from sqlalchemy import create_engine
from transformers import BertTokenizer, TFBertForSequenceClassification, TFBertModel

# Load .env file
load_dotenv()

# nltk downloads (you may need more depending on your usage)
nltk.download('punkt')
nltk.download('stopwords')

# Load Spacy model (you may need to download this first with `python -m spacy download en_core_web_sm`)
nlp = spacy.load('en_core_web_sm')


# Define the model
model = TFBertForSequenceClassification.from_pretrained(
    "bert-base-uncased", num_labels=2
)

# Define the optimizer, loss function, and metrics
optimizer = tf.keras.optimizers.Adam(learning_rate=2e-5, epsilon=1e-08)
loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')

model.compile(optimizer=optimizer, loss=loss, metrics=[metric])
