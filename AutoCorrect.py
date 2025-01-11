from flask import Flask, request, jsonify, render_template
from symspellpy.symspellpy import SymSpell, Verbosity
import os
import re

app = Flask(__name__)

# Initialize SymSpell for Vietnamese
def initialize_symspell(language="en"):
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    dictionary_path = f"Resources/frequency_dictionary_{language}.txt"
    if os.path.exists(dictionary_path):
        sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    else:
        raise FileNotFoundError(f"Dictionary file not found at {dictionary_path}")
    return sym_spell

# Load both English and Vietnamese dictionaries
sym_spell_dict = {
    "en": initialize_symspell("en"),
    "vi": initialize_symspell("vi")
}

# Correct the last word based on the selected language
def autocorrect_last_word(input_text, language="en"):
    sym_spell = sym_spell_dict.get(language, sym_spell_dict["en"])
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
    try:
        data = request.json
        input_text = data.get("text", "")
        event_type = data.get("event_type", "")
        language = data.get("language", "en")  # Default to English

        if event_type == "space":
            corrected_text = autocorrect_last_word(input_text, language)
            return jsonify({"corrected_text": corrected_text})

        return jsonify({"corrected_text": input_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Backend route to handle command execution
@app.route('/process_command', methods=['POST'])
def process_command():
    try:
        data = request.form.get("user_input", "").strip()

        # YouTube search
        youtube_match = re.match(r"youtube search\s*(.*)", data, re.IGNORECASE)
        if youtube_match:
            query = youtube_match.group(1)
            youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            return jsonify({"status": "success", "redirect_url": youtube_url})

        # Google search
        google_match = re.match(r"google search\s*(.*)", data, re.IGNORECASE)
        if google_match:
            query = google_match.group(1)
            google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            return jsonify({"status": "success", "redirect_url": google_url})

        return jsonify({"status": "error", "message": "Invalid command"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Home route to render the HTML page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    port = os.environ.get("PORT", 5000)
    app.run(debug=False, host="0.0.0.0", port=int(port))
