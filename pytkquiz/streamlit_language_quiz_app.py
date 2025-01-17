import logging
import os
import streamlit as st
from PIL import Image
# import gtts
# import base64

from streamlit.components.v1 import html
from streamlit_card import card

from feedback import show_feedback_ui
from sound_gen import generate_sound_if_not_found
from quiz_logic import QuizLogic, WordData


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


class StreamlitLanguageQuizApp:
    def __init__(self):
        self.audio_button = None
        self.question_fragment = None
        self.root_dir = os.path.abspath(os.path.join(__file__, "..", ".."))
        self.quiz_logic = QuizLogic(root_dir=self.root_dir)
        self.language = 'en'

        self.update_language(load_next=False)

        if 'current_question' not in st.session_state:
            self.next_question()
        else:
            self.quiz_logic.current_question = st.session_state.current_question
            self.quiz_logic.options = st.session_state.options
            self.quiz_logic.score = st.session_state.score
            self.quiz_logic.attempts = st.session_state.attempts

    def update_language(self, load_next=True):
        if self.language == "en":
            words_path = os.path.join(self.root_dir, "words.csv")
        else:
            words_path = os.path.join(self.root_dir, "words_" + self.language + ".csv")
        word_col_index = 0 if self.language == "en" else 4
        self.quiz_logic = QuizLogic(root_dir=self.root_dir, language=self.language)
        self.quiz_logic.load_word_data(words_path, word_col_index)

        if load_next:
            self.next_question()

    def next_question(self):
        options = self.quiz_logic.next_question()
        st.session_state.current_question = self.quiz_logic.current_question
        st.session_state.options = options
        st.session_state.answered = False
        st.session_state.message = ''
        st.session_state.score = self.quiz_logic.score
        st.session_state.attempts = self.quiz_logic.attempts

    @st.fragment
    def show_word(self):

        lang_name = st.selectbox(
            "Select Language:",
            ['English', 'Ελληνικά'],
            index=0,
            key="language_selectbox"
        )
        lang_map = {
            'English': 'en',
            'Ελληνικά': 'el'
        }
        language = lang_map[lang_name]

        if self.language != language:
            self.language = language
            self.update_language()

        c1, c2 = st.columns(2)

        with c1:
            st.metric("Score", st.session_state.score)
        with c2:
            st.metric("Attempts", st.session_state.attempts)

        _ = card(
            title=st.session_state.current_question.word,
            text="",
            styles={
                "card": {
                    "width": "100%",
                    "height": "200px",
                    "border-radius": "40px",
                    "box-shadow": "0 0 10px rgba(0,0,0,0.5)",
                    "background-color": "#fff",
                    "font-size": "48px!important;",
                    "font-weight": "bold!important",
                    "font-family": "Arial, sans-serif!important",
                },
                "title": {
                    "color": "#0000c0",
                    "background-color": "#fff",
                },
                "filter": {
                    "background-color": "rgba(0, 0, 0, 0)"  # <- make the image not dimmed anymore
                }
            },
        )

        # Display images
        cols = st.columns(3)
        for i, option in enumerate(st.session_state.options):
            with cols[i]:
                image_path = self.quiz_logic.image_path_for_word(option)
                image = Image.open(image_path)
                st.image(image, use_column_width=True)
                self.audio_element_for_word(option)

                if st.button(f"Select", key=f"select_{i}"):
                    if not st.session_state.answered:
                        self.check_answer(option)
                    # TODO: get this to not let them change their answer.

        # Display message
        if 'message' in st.session_state:
            st.write(st.session_state.message)

        # Next question button
        if st.session_state.get('answered', False):
            if st.button("Next Question"):
                self.next_question()
                st.rerun(scope="fragment")

    def run(self):
        st.title("Sight Words Quiz")
        show_feedback_ui()
        self.show_word()

    def check_answer(self, selected_option: WordData):
        correct = self.quiz_logic.check_answer(selected_option)
        if correct:
            st.session_state.message = f"That's correct! \n\nDefinition: {st.session_state.current_question.definition}"
            self.speak_text("Yes, that's correct!")
            st.balloons()
        else:
            st.session_state.message = f"""Sorry, that's incorrect. The correct answer was {st.session_state.current_question.word}.
            Definition: {st.session_state.current_question.definition}"""
            self.speak_text("Sorry, that's incorrect!")
            st.subheader("Sorry :sob:")

        st.session_state.score = self.quiz_logic.score
        st.session_state.attempts = self.quiz_logic.attempts
        st.session_state.answered = True

    def audio_element_for_word(self, word: WordData):
        sound_path = self.quiz_logic.sound_path_for_word(word)
        return self.show_audio(sound_path, word.word)

    def speak_text(self, text: str):
        safe_name = ''.join(c if c.isalnum() else "_" for c in text)
        sound_path = os.path.join(self.root_dir, "word_sounds", safe_name.lower() + ".mp3")
        return self.show_audio(sound_path, safe_name, hidden=True, autoplay=True)

    def show_audio(self, sound_path, word, hidden=False, autoplay=False):
        generate_sound_if_not_found(self.language, word, sound_path)
        audio_file = open(sound_path, 'rb')
        audio_bytes = audio_file.read()
        st.write("""
                  <style>
                    div[data-testid="stVerticalBlockBorderWrapper"]:has(
                      >div>div>div[data-testid="element-container"] 
                      .hide-the-container
                    ) {
                      display: none; 
                    }
                  </style>
                  """, unsafe_allow_html=True)

        with st.container():
            audio_elem = st.audio(audio_bytes, format='audio/mpeg', autoplay=autoplay)
            if hidden:
                st.write('<span class="hide-the-container"/>', unsafe_allow_html=True)

        return audio_elem


if __name__ == "__main__":
    app = StreamlitLanguageQuizApp()
    app.run()
