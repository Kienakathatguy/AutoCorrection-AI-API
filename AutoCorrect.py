from flask import Flask, request, jsonify, render_template
from symspellpy.symspellpy import SymSpell, Verbosity
import os
import re
import webbrowser


app = Flask(__name__)


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


    # Split text into words, correct only the last word
    words = input_text.split()
    last_word = words[-1] if words else ""
    suggestions = sym_spell.lookup(last_word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions:
        words[-1] = suggestions[0].term
    return " ".join(words)


# Backend route for real-time autocorrection
@app.route('/realtime_autocorrect', methods=['POST'])
def realtime_autocorrect():
    data = request.json
    input_text = data.get("text", "")
    event_type = data.get("event_type", "")


    if event_type == "space":
        corrected_text = autocorrect_last_word(sym_spell, input_text)
        return jsonify({"corrected_text": corrected_text})


    return jsonify({"corrected_text": input_text})


# Backend route to handle command execution
@app.route('/process_command', methods=['POST'])
def process_command():
    data = request.form.get("user_input", "").strip()

    # Check for YouTube search command
    youtube_match = re.match(r"youtube search\s*(.*)", data, re.IGNORECASE)
    if youtube_match:
        query = youtube_match.group(1)
        youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        return jsonify({"status": "success", "redirect_url": youtube_url})

    # Check for Google search command
    google_match = re.match(r"google search\s*(.*)", data, re.IGNORECASE)
    if google_match:
        query = google_match.group(1)
        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return jsonify({"status": "success", "redirect_url": google_url})

     # Check for Gmail compose command
    mail_match = re.match(r"mail\s+([\w.%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})", data, re.IGNORECASE)
    if mail_match:
        email_address = mail_match.group(1)
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={email_address}"
        return jsonify({"status": "success", "redirect_url": gmail_url})

    # Check for Facebook command
    if data.lower() == "facebook":
        facebook_url = "https://www.facebook.com"
        return jsonify({"status": "success", "redirect_url": facebook_url})

    return jsonify({"status": "error", "message": "Invalid command"})


# Home route to render the HTML page
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
     # Use `PORT` environment variable if set; default to 5000 for local development
    port = os.environ.get("PORT", 5000)
    # Bind to `0.0.0.0` to make it accessible on Render
    app.run(debug=False, host="0.0.0.0", port=int(port))
