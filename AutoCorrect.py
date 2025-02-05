from flask import Flask, request, jsonify, render_template
import os
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Function to correct text using LanguageTool API
def correct_text(input_text):
    if not input_text.strip():
        return input_text

    url = "https://api.languagetool.org/v2/check"
    data = {"text": input_text, "language": "en-US"}

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()

        corrected_text = input_text
        for match in reversed(result.get("matches", [])):  # Reverse to prevent offset issues
            offset = match["context"]["offset"]
            length = match["context"]["length"]
            replacement = match["replacements"][0]["value"] if match["replacements"] else corrected_text[offset:offset+length]
            corrected_text = corrected_text[:offset] + replacement + corrected_text[offset+length:]

        return corrected_text

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return input_text  # Return original text if correction fails

# API route for real-time autocorrection
@app.route('/realtime_autocorrect', methods=['POST'])
def realtime_autocorrect():
    data = request.json
    input_text = data.get("text", "")
    corrected_text = correct_text(input_text)
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
