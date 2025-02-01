from flask import Flask, request, jsonify, render_template
import os
import requests
from symspellpy.symspellpy import SymSpell, Verbosity
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize SymSpell
def initialize_symspell():
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    dictionary_path = "Resources/frequency_dictionary_en.txt"
    if os.path.exists(dictionary_path):
        sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    else:
        raise FileNotFoundError(f"Dictionary file not found at {dictionary_path}")
    return sym_spell

sym_spell = initialize_symspell()

# Correct the last word in the text
def autocorrect_last_word(sym_spell, input_text):
    if not input_text.strip():
        return input_text

    words = input_text.split()
    last_word = words[-1] if words else ""
    suggestions = sym_spell.lookup(last_word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions:
        words[-1] = suggestions[0].term
    return " ".join(words)

# Backend route for real-time autocorrection
@app.route('/realtime_autocorrect', methods=['POST'])
def realtime_autocorrect():
    data = request.json  # Request data coming from frontend
    input_text = data.get("text", "")
    corrected_text = autocorrect_last_word(sym_spell, input_text)
    return jsonify({"corrected_text": corrected_text})

# Backend route to fetch weather data
@app.route('/weather', methods=['GET'])
def fetch_weather():
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

# New backend route to handle "compose mail" command
@app.route('/compose_mail', methods=['POST'])
def compose_mail():
    data = request.json

    # Extract the fields
    recipient = data.get("to", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()

    # Validate the fields
    if not recipient:
        return jsonify({"error": "Recipient (to) is required"}), 400
    if not subject:
        return jsonify({"error": "Subject is required"}), 400
    if not body:
        return jsonify({"error": "Body is required"}), 400

    # Construct the Gmail compose URL
    gmail_url = (
        f"https://mail.google.com/mail/?view=cm&fs=1&to={recipient}"
        f"&su={subject}&body={body}"
    )
    return jsonify({"gmail_url": gmail_url})

# Home route to render the HTML page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    port = os.environ.get("PORT", 5000)
    app.run(debug=False, host="0.0.0.0", port=int(port))
