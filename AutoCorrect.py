from flask import Flask, request, jsonify, render_template
import os
import requests
import spacy
import time
import re
import nltk
from nltk.stem import WordNetLemmatizer
from flask_cors import CORS
import language_tool_python

# Download necessary NLTK data
nltk.download("wordnet")

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)

# Constants
LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"
debounce_time = 0.2  # Debounce time in seconds to prevent too many requests
last_request_time = 0  # Timestamp for last API call

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize LanguageTool
tool = language_tool_python.LanguageTool("en-US")

# Initialize NLTK Lemmatizer
lemmatizer = WordNetLemmatizer()

# Function to detect tense based on time markers
def detect_tense(input_text):
    """Determine if the sentence is in past or present tense based on context."""
    past_tense_keywords = ['yesterday', 'ago', 'last', 'past', 'then']
    
    if any(keyword in input_text.lower() for keyword in past_tense_keywords):
        return "past"
    return "present"

# Function to conjugate verbs based on tense and subject
def conjugate_verb(verb, tense, subject):
    """Returns the verb conjugated based on tense and subject."""
    if tense == "past":
        # Handle regular past tense by adding 'ed' (simplified for regular verbs)
        if verb.endswith('e'):
            return verb + 'd'  # e.g., "make" -> "made"
        else:
            return verb + 'ed'  # e.g., "run" -> "runned" (we'll fix this later for irregulars)
    
    elif tense == "present":
        # Singular subject (he, she, it)
        if subject in ["he", "she", "it"]:
            return verb + "s"  # e.g., "run" -> "runs"
        else:
            return verb  # For plural subjects (they, we), use base form
    return verb

# Function to correct subject-verb agreement
def correct_subject_verb_agreement(doc):
    corrected_text = []
    
    for token in doc:
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            subject = None
            for child in token.children:
                if child.dep_ == "nsubj":
                    subject = child
            
            if subject:
                tense = detect_tense(" ".join([token.text for token in doc]))
                corrected_verb = conjugate_verb(token.text, tense, subject.text)
                corrected_text.append(corrected_verb)
            else:
                corrected_text.append(token.text)
        else:
            corrected_text.append(token.text)
    
    return " ".join(corrected_text)

# Function to apply grammar corrections via LanguageTool with error handling and debounce
def grammar_check(input_text):
    global last_request_time
    current_time = time.time()
    
    # Apply debounce logic to prevent multiple rapid requests
    if current_time - last_request_time < debounce_time:
        return input_text

    last_request_time = current_time
    
    # Prepare data for LanguageTool API
    data = {"text": input_text, "language": "en-US"}
    try:
        response = requests.post(LANGUAGETOOL_API_URL, data=data)
        response.raise_for_status()  # Check if the request was successful
        result = response.json()

        # Apply corrections
        for match in reversed(result.get("matches", [])):
            offset = match["offset"]
            length = match["length"]
            replacement = match["replacements"][0]["value"] if match["replacements"] else input_text[offset:offset + length]
            input_text = input_text[:offset] + replacement + input_text[offset + length:]

        return input_text
    except requests.exceptions.RequestException as e:
        print(f"Error in LanguageTool API: {e}")
        # In case of failure, return the original input text
        return input_text

# Function to handle the overall text correction
def correct_tense(input_text):
    """Corrects verb tenses based on subject and context."""
    doc = nlp(input_text)
    corrected_text = []
    
    for token in doc:
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            subject = None
            for child in token.children:
                if child.dep_ == "nsubj":
                    subject = child
            
            tense = detect_tense(input_text)  # Detect tense (past/present)
            corrected_verb = conjugate_verb(token.text, tense, subject.text if subject else "")
            corrected_text.append(corrected_verb)
        else:
            corrected_text.append(token.text)
    
    corrected_text = " ".join(corrected_text)
    corrected_text = correct_subject_verb_agreement(doc)  # Ensure subject-verb agreement
    corrected_text = grammar_check(corrected_text)  # Apply grammar check via LanguageTool
    
    return corrected_text

@app.route('/correct_text', methods=['POST'])
def correct_text():
    """Handles grammar correction on full sentences."""
    data = request.json
    input_text = data.get("text", "").strip()
    if not input_text:
        return jsonify({"corrected_text": input_text})

    corrected_text = correct_tense(input_text)
    return jsonify({"corrected_text": corrected_text})

@app.route('/weather', methods=['GET'])
def fetch_weather():
    """Fetches weather for a given location."""
    location = request.args.get("location")
    if not location:
        return jsonify({"error": "Location is required"}), 400

    url = f"https://wttr.in/{location}?format=%C"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return jsonify({"weather": response.text.strip()})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch weather: {str(e)}"}), 500

@app.route('/compose_mail', methods=['POST'])
def compose_mail():
    """Generates a Gmail compose URL with recipient, subject, and body."""
    data = request.json
    recipient = data.get("to", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()

    if not recipient:
        return jsonify({"error": "Recipient (to) is required"}), 400
    if not subject:
        return jsonify({"error": "Subject is required"}), 400
    if not body:
        return jsonify({"error": "Body is required"}), 400

    gmail_url = (
        f"https://mail.google.com/mail/?view=cm&fs=1&to={recipient}"
        f"&su={subject}&body={body}"
    )
    return jsonify({"gmail_url": gmail_url})

@app.route('/')
def index():
    """Renders the homepage."""
    return render_template('index.html')

if __name__ == "__main__":
    port = os.environ.get("PORT", 5000)
    app.run(debug=True, host="0.0.0.0", port=int(port))
