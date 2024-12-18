import streamlit as st
from vocab_manager import GermanVocabManager

class GermanVocabApp:
    def __init__(self):
        self.vocab_manager = GermanVocabManager()
        self.setup_page()
        self.initialize_session_state()
        self.apply_custom_css()

    def setup_page(self):
        """Configure the Streamlit page"""
        st.set_page_config(page_title="German Vocabulary Review", layout="wide")

    def initialize_session_state(self):
        """Initialize all session state variables"""
        if 'vocabulary' not in st.session_state:
            st.session_state.vocabulary = self.vocab_manager.load_vocabulary()
        if 'current_word_index' not in st.session_state:
            st.session_state.current_word_index = None
        if 'user_answer' not in st.session_state:
            st.session_state.user_answer = ''
        if 'answer_submitted' not in st.session_state:
            st.session_state.answer_submitted = False
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = False
        if 'llm_response' not in st.session_state:
            st.session_state.llm_response = ''
        if 'consecutive_new_incorrect' not in st.session_state:
            st.session_state.consecutive_new_incorrect = 0

    def apply_custom_css(self):
        """Apply custom CSS styling"""
        st.markdown("""
            <style>
            .main-title {
                font-size: 48px;
                color: #2E4053;
                font-weight: bold;
                text-align: center;
                margin-bottom: 30px;
                font-family: 'Arial', sans-serif;
            }
            .stButton > button {
                width: 100%;
                background-color: #f4f6f7;
                color: #2E4053;
                font-size: 18px;
                font-weight: bold;
                padding: 15px 0;
                border: none;
                border-radius: 5px;
                margin-bottom: 10px;
                transition: all 0.3s ease;
            }
            .stButton > button:hover {
                background-color: #d4efdf;
                color: #27ae60;
            }
            .question-box {
                background-color: #F4F6F7;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }
            .answer-box {
                background-color: #E8F8F5;
                padding: 15px;
                border-radius: 10px;
                margin-top: 10px;
                margin-bottom: 20px;
            }
            .llm-response-box {
                background-color: #F0F3F4;
                padding: 15px;
                border-radius: 10px;
                margin-top: 20px;
                border: 1px solid #D5DBDB;
            }
            div[data-baseweb="select"] {
                min-height: 48px;
            }
            div[data-baseweb="select"] > div {
                min-height: 48px;
                font-size: 16px !important;
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 5px 10px;
            }
            ul[role="listbox"] li {
                min-height: 40px;
                padding: 8px 16px;
                font-size: 16px !important;
            }
            .stSelectbox > div {
                padding: 5px;
                margin-bottom: 15px;
            }
            .stTextArea > div > div > textarea {
                background-color: #f8f9fa;
                border-radius: 5px;
                min-height: 100px;
                font-size: 16px;
            }
            .stSelectbox > div > div[role="listbox"] {
                height: auto;
                max-height: 300px;
            }
            </style>
        """, unsafe_allow_html=True)

    def show_all_vocabulary(self):
        """Display all vocabulary"""
        st.header("All Vocabulary")
        for i, word in enumerate(st.session_state.vocabulary, 1):
            with st.expander(f"{i}. {word['word']} ({word['part_of_speech']})"):
                if word['part_of_speech'] == 'noun':
                    st.write(f"**Gender:** {word['gender']}")
                st.write(f"**Definition:** {word['definition']}")
                st.write(f"**Current Example:** {word['example']}")
                if word.get('previous_example'):
                    st.write(f"**Previous Example:** {word['previous_example']}")
                st.write(f"**Times Asked:** {word.get('times_asked', 0)}")
                st.write(f"**Category:** {word.get('category', 'new')}")

    def add_vocabulary(self):
        """Add new vocabulary"""
        st.header("Add New Vocabulary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_word = st.text_input("🔤 German Word:")
            pos_options = ["noun", "verb", "adjective", "adverb", "preposition", "conjunction", "other", "phrase"]
            part_of_speech = st.selectbox("📝 Part of Speech:", pos_options)
            
            if part_of_speech == "noun":
                gender = st.selectbox("⚥ Gender:", ["der (masculine)", "die (feminine)", "das (neutral)"])
            else:
                gender = None
                
        with col2:
            definition = st.text_area("📚 Definition:")
            example = st.text_area("✏️ Example sentence:")

        if st.button("➕ Add Word"):
            if new_word and definition and example:
                new_entry = self.vocab_manager.create_new_word_entry(
                    word=new_word,
                    part_of_speech=part_of_speech,
                    definition=definition,
                    example=example,
                    gender=gender
                )
                st.session_state.vocabulary.append(new_entry)
                self.vocab_manager.save_vocabulary(st.session_state.vocabulary)
                st.success("✅ Word added successfully!")
            else:
                st.warning("⚠️ Please fill in all required fields.")

    def practice_mode(self):
        """Practice vocabulary"""
        st.header("Practice Vocabulary")

        if st.session_state.vocabulary:
            if st.session_state.current_word_index is None:
                st.session_state.current_word_index = self.vocab_manager.get_next_word_index(
                    st.session_state.vocabulary, 
                    st.session_state.consecutive_new_incorrect
                )
                st.session_state.user_answer = ''
                st.session_state.answer_submitted = False
                st.session_state.show_answer = False
                st.session_state.llm_response = ''

            word_entry = st.session_state.vocabulary[st.session_state.current_word_index]

            if not st.session_state.answer_submitted:
                self.vocab_manager.increment_times_asked(word_entry)

            st.markdown(
                f'<div class="question-box"><b>Word:</b> {word_entry["word"]}<br>'
                f'<b>Example:</b> {word_entry["example"]}</div>', 
                unsafe_allow_html=True
            )

            col1, col2 = st.columns([1, 2])
            
            with col1:
                if st.button("👀 Show Answer"):
                    st.session_state.show_answer = True

            if st.session_state.show_answer:
                answer_text = f"**Definition:** {word_entry['definition']}"
                if word_entry['part_of_speech'] == 'noun':
                    answer_text = f"**Gender:** {word_entry['gender']}<br>{answer_text}"
                st.markdown(f'<div class="answer-box">{answer_text}</div>', unsafe_allow_html=True)
                if word_entry.get('previous_example'):
                    st.info(f"Previous example: {word_entry['previous_example']}")

            if not st.session_state.answer_submitted:
                with st.form(key='answer_form'):
                    if word_entry['part_of_speech'] == 'noun':
                        gender_answer = st.selectbox(
                            "⚥ Gender:", 
                            ["der (masculine)", "die (feminine)", "das (neutral)"], 
                            key="gender_answer"
                        )
                    definition_answer = st.text_area("✍️ Your Definition:", key="user_answer_input")
                    submit_button = st.form_submit_button("📤 Submit Answer")
                    
                    if submit_button:
                        if definition_answer:
                            if word_entry['part_of_speech'] == 'noun':
                                st.session_state.user_answer = f"Gender: {gender_answer}\nDefinition: {definition_answer}"
                            else:
                                st.session_state.user_answer = definition_answer
                            st.session_state.answer_submitted = True
                            st.rerun()
                        else:
                            st.warning("⚠️ Please provide an answer.")

            if st.session_state.answer_submitted and not st.session_state.llm_response:
                st.info("⏳ Evaluating your answer, please wait...")
                llm_response = self.vocab_manager.check_answer(word_entry, st.session_state.user_answer)
                st.session_state.llm_response = llm_response

                new_category = self.vocab_manager.categorize_answer(llm_response)
                if new_category != "correct":
                    st.session_state.consecutive_new_incorrect += 1
                else:
                    st.session_state.consecutive_new_incorrect = 0

                word_entry['category'] = new_category
                self.vocab_manager.save_vocabulary(st.session_state.vocabulary)

            if st.session_state.llm_response:
                st.markdown(f'<div class="llm-response-box">{st.session_state.llm_response}</div>', 
                          unsafe_allow_html=True)

            with col2:
                if st.button("Next Word ➡️"):
                    st.session_state.current_word_index = None
                    st.rerun()
        else:
            st.warning("No vocabulary available. Please add some words first.")

    def edit_vocabulary(self):
        """Edit existing vocabulary"""
        st.header("Edit Vocabulary")
        
        # Define part of speech options consistently
        pos_options = ["noun", "verb", "adjective", "adverb", "preposition", "conjunction", "other", "phrase"]

        for i, word in enumerate(st.session_state.vocabulary):
            with st.expander(f"{word['word']} ({word['part_of_speech']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_word = st.text_input("Edit Word", word['word'], key=f"edit_w_{i}")
                    try:
                        current_pos_index = pos_options.index(word['part_of_speech'])
                    except ValueError:
                        current_pos_index = 0
                    
                    new_pos = st.selectbox(
                        "Part of Speech", 
                        pos_options,
                        index=current_pos_index,
                        key=f"edit_pos_{i}"
                    )
                    
                    new_gender = None
                    if new_pos == "noun":
                        gender_options = ["der (masculine)", "die (feminine)", "das (neutral)"]
                        current_gender = word.get('gender', "der (masculine)")
                        try:
                            current_gender_index = gender_options.index(current_gender)
                        except ValueError:
                            current_gender_index = 0
                            
                        new_gender = st.selectbox(
                            "Gender", 
                            gender_options,
                            index=current_gender_index,
                            key=f"edit_gender_{i}"
                        )

                with col2:
                    new_definition = st.text_area("Edit Definition", word['definition'], key=f"edit_def_{i}")
                    new_example = st.text_area("Edit Example", word['example'], key=f"edit_ex_{i}")
                    
                    category_options = ['new', 'correct', 'incorrect']
                    current_category = word.get('category', 'new')
                    try:
                        current_category_index = category_options.index(current_category)
                    except ValueError:
                        current_category_index = 0
                        
                    new_category = st.selectbox(
                        "Category", 
                        category_options,
                        index=current_category_index,
                        key=f"edit_cat_{i}"
                    )

                col3, col4 = st.columns(2)
                with col3:
                    if st.button("Save Changes", key=f"save_{i}"):
                        st.session_state.vocabulary[i] = self.vocab_manager.update_word_entry(
                            word_entry=word,
                            word=new_word,
                            part_of_speech=new_pos,
                            definition=new_definition,
                            example=new_example,
                            gender=new_gender
                        )
                        self.vocab_manager.save_vocabulary(st.session_state.vocabulary)
                        st.success("✅ Changes saved successfully!")

                with col4:
                    if st.button("Delete Word", key=f"delete_{i}"):
                        st.session_state.vocabulary.pop(i)
                        self.vocab_manager.save_vocabulary(st.session_state.vocabulary)
                        st.warning("❗ Word deleted.")
                        st.rerun()

    def run(self):
        """Run the Streamlit app"""
        st.markdown('<div class="main-title">German Vocabulary Review 🇩🇪📚</div>', unsafe_allow_html=True)
        
        mode = st.sidebar.radio(
            "Choose Mode",
            ["Add Vocabulary 📝", "Edit Vocabulary ✏️", "Practice 🎯", "Review All 📖"],
            key="mode_selector"
        )

        if mode == "Add Vocabulary 📝":
            self.add_vocabulary()
        elif mode == "Edit Vocabulary ✏️":
            self.edit_vocabulary()
        elif mode == "Practice 🎯":
            self.practice_mode()
        elif mode == "Review All 📖":
            self.show_all_vocabulary()

if __name__ == "__main__":
    app = GermanVocabApp()
    app.run()
