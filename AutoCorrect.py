from flask import Flask, request, jsonify, render_template
import os
import requests
from flask_cors import CORS
import spacy
import language_tool_python
from nltk.stem import WordNetLemmatizer
import nltk
import time
import re

# Download necessary NLTK data
nltk.download("wordnet")

app = Flask(__name__)
CORS(app)

LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# Initialize LanguageTool for grammar corrections
tool = language_tool_python.LanguageTool("en-US")

# Initialize NLTK Lemmatizer
lemmatizer = WordNetLemmatizer()

debounce_time = 0.2  # Debounce time in seconds
last_request_time = 0  # Timestamp for last API call


def detect_tense(tokens):
    """Determines the tense of the sentence based on verb usage."""
    past_tense = False
    present_tense = False
    future_tense = False

    for token in tokens:
        if token.tag_ in ["VBD", "VBN"]:  # Past tense verbs
            past_tense = True
        elif token.tag_ in ["VBP", "VBZ", "VBG"]:  # Present tense verbs
            present_tense = True
        elif token.text.lower() in ["will", "shall"]:  # Future tense
            future_tense = True

    if future_tense:
        return "future"
    elif past_tense:
        return "past"
    elif present_tense:
        return "present"
    return "unknown"


def correct_tense(input_text):
    """Corrects verb tenses using spaCy and NLTK."""
    doc = nlp(input_text)
    corrected_text = []
    
    # Time markers indicating past tense
    past_tense_keywords = ['yesterday', 'ago', 'last', 'past']
    
    # Detect if we need to apply past tense (based on time markers like 'yesterday')
    is_past_tense = any(keyword in input_text.lower() for keyword in past_tense_keywords)

    for token in doc:
        # Check if the token is a verb and its dependency is 'ROOT' (main verb in the sentence)
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            subject = None
            # Find the subject of the verb (look for nsubj dependency)
            for child in token.children:
                if child.dep_ == "nsubj":
                    subject = child
            
            # Correct verb tense based on subject (singular/plural) and time context (past/future)
            if subject:
                # Handle singular subject (he, she, it)
                if subject.tag_ in ["PRP", "VBZ"]:  # Singular subject like "he", "she"
                    if is_past_tense:
                        # Convert verb to past tense
                        corrected_text.append(lemmatizer.lemmatize(token.text, 'v') + "ed")  # Convert to past tense
                    else:
                        # Keep verb in base form for singular subjects
                        if token.text.lower() != token.lemma_.lower():
                            corrected_text.append(token.lemma_)  # Use base form for singular subjects
                        else:
                            corrected_text.append(token.text)
                else:  # Handle plural subjects like "they", "we"
                    if token.text.lower() == token.lemma_.lower():
                        corrected_text.append(token.text)
                    else:
                        corrected_text.append(token.lemma_)
            else:
                corrected_text.append(token.text)
        else:
            corrected_text.append(token.text)
        
        # Fix modal verbs (like "will", "can", etc.) followed by the base form
        if token.dep_ == 'aux' and token.text.lower() in ['will', 'can', 'should', 'may']:
            next_token = token.nbor()
            if next_token.pos_ == 'VERB' and next_token.text.endswith('s'):
                corrected_text[-1] = token.lemma_  # Use the base form for modal verbs
                corrected_text.append(lemmatizer.lemmatize(next_token.text, 'v'))  # Use base form for verb
        
        # Fix contractions like "don't" to "doesn't"
        if token.text.lower() == "don't" and subject and subject.tag_ == "PRP" and subject.text.lower() not in ['i', 'we', 'you', 'they']:
            corrected_text[-1] = "doesn't"  # Change "don't" to "doesn't"
    
    # Handle missing "is" for sentences like "The cat on the table."
    if "on" in input_text.lower() and "table" in input_text.lower() and "is" not in input_text.lower():
        corrected_text.insert(0, "is")
    
    return " ".join(corrected_text).strip()

def custom_grammar_check(input_text):
    """Applies custom grammar rules before sending to LanguageTool."""
    input_text = re.sub(r"\bi\b", "I", input_text)  # Capitalizing 'I'
    return input_text


def grammar_check(input_text):
    """Applies grammar corrections via LanguageTool, with corrections after periods."""
    global last_request_time
    current_time = time.time()
    if current_time - last_request_time < debounce_time:
        return input_text

    last_request_time = current_time
    input_text = custom_grammar_check(input_text)

    sentences = re.split(r"(\. )", input_text)  # Split on periods while keeping them

    corrected_sentences = []
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]  # Keep the period
        else:
            sentence = sentences[i]

        data = {"text": sentence, "language": "en-US"}
        try:
            response = requests.post(LANGUAGETOOL_API_URL, data=data)
            response.raise_for_status()
            result = response.json()

            for match in reversed(result.get("matches", [])):
                offset = match["offset"]
                length = match["length"]
                replacement = match["replacements"][0]["value"] if match["replacements"] else sentence[offset:offset+length]
                sentence = sentence[:offset] + replacement + sentence[offset+length:]

            corrected_sentences.append(sentence)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            corrected_sentences.append(sentence)

    return "".join(corrected_sentences)


@app.route('/correct_text', methods=['POST'])
def correct_text():
    """Handles grammar correction on full sentences."""
    data = request.json
    input_text = data.get("text", "").strip()
    if not input_text:
        return jsonify({"corrected_text": input_text})

    corrected_text = correct_tense(input_text)
    corrected_text = grammar_check(corrected_text)
    
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
