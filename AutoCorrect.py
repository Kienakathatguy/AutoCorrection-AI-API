import streamlit as st
from symspellpy.symspellpy import SymSpell, Verbosity
import os

# Initialize SymSpell
@st.cache_resource
def initialize_symspell():
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    dictionary_path = "Resources/frequency_dictionary_en_82_765.txt"
    if os.path.exists(dictionary_path):
        sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    else:
        st.error("Dictionary file not found. Please check the path.")
    return sym_spell

# Correct only the last word in the text
def autocorrect_last_word(sym_spell, input_text):
    if not input_text.strip():
        return input_text  # Return if input is empty or only spaces

    words = input_text.split()
    last_word = words[-1] if words else ""
    suggestions = sym_spell.lookup(last_word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions:
        words[-1] = suggestions[0].term  # Replace the last word with its correction
    return " ".join(words)

# Handle key release and autocorrection
def autocorrect_on_input(sym_spell, user_input):
    if user_input.strip():
        corrected_text = autocorrect_last_word(sym_spell, user_input)
    else:
        corrected_text = user_input
    return corrected_text

# Streamlit app
def main():
    st.title("Realtime Sentence Autocorrection")
    st.write("Type your text below, and we'll autocorrect it in real-time!")

    # Load SymSpell
    sym_spell = initialize_symspell()

    # Text Input Field
    user_input = st.text_area("Enter text:", value="", height=200, key="input_text")

    # Process input and show autocorrected text
    corrected_text = autocorrect_on_input(sym_spell, user_input)
    st.subheader("Corrected Text")
    st.text_area("Output:", value=corrected_text, height=200, disabled=True)

if __name__ == "__main__":
    main()
