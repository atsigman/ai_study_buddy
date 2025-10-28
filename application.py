"""
Main application logic.
"""

import os
import streamlit as st

from dotenv import load_dotenv

from src.generator.question_generator import QuestionGenerator
from src.utils.helpers import rerun, QuizManager


load_dotenv()


def main() -> None:
    st.set_page_config(page_title="AI Study Buddy", page_icon="📚🤖")

    if "quiz_manager" not in st.session_state:
        st.session_state.quiz_manager = QuizManager()

    if "quiz_generated" not in st.session_state:
        st.session_state.quiz_generated = False

    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    if "rerun_trigger" not in st.session_state:
        st.session_state.rerun_trigger = False

    st.title("AI Study Buddy")
    st.sidebar.header("Quiz Settings")

    question_type = st.sidebar.selectbox(
        "Question Type",
        ["Multiple Choice", "Fill in the Blank"],
        index=0
    )

    topic = st.sidebar.text_input(
        "Enter Topic",
        placeholder = "AI History, Technology"
    )

    difficulty = st.sidebar.selectbox(
        "Difficulty Level",
        ["Easy", "Medium", "Hard"],
        index=1
    )

    n_questions = st.sidebar.number_input(
        "Number of Questions",
        min_value=1,
        max_value=10,
        value=5
    )

    # Generate quiz:
    if st.sidebar.button("Generate Quiz"):
        st.session_state.quiz_submitted = False

        generator = QuestionGenerator()
        success = st.session_state.quiz_manager.generate_questions(
            generator, topic, question_type, difficulty, n_questions
        )

        st.session_state.quiz_generated = success
        # Reflect changes in UI:
        rerun()

    # Attempt quiz:
    if st.session_state.quiz_generated and st.session_state.quiz_manager.questions:
        st.header("Quiz")
        st.session_state.quiz_manager.attempt_quiz()

        if st.button("Submit Quiz"):
            st.session_state.quiz_manager.evaluate_quiz()
            st.session_state.quiz_submitted = True
            rerun()

    if st.session_state.quiz_submitted:
        st.header("Quiz Results")
        results_df = st.session_state.quiz_manager.generate_result_dataframe()

        if not results_df.empty:
            correct_count = results_df["is_correct"].sum()
            score_perc =  (correct_count / len(results_df)) * 100
            st.write(f"Score: {score_perc}%")

        # Iterate through questions, print evaluation for each:
        for _, result in results_df.iterrows():
            question_num = result["question_number"]
            if result["is_correct"]:
                st.success(f"✅ Question {question_num}: {result['question']}")
                st.write(f"Your answer: {result['user_answer']}")

            else:
                st.error(f"❌ Question {question_num}: {result['question']}")
                st.write(f"Your answer: {result['user_answer']}")
                st.write(f"Correct answer: {result['correct_answer']}")

            st.markdown("--------")

        # Save/download results:
        if st.button("Save Results"):
            output_filepath = st.session_state.quiz_manager.save_to_csv()
            if output_filepath:
                with open(output_filepath, "rb") as f:
                    st.download_button(
                        label="Download Results",
                        data=f.read(),
                        file_name=os.path.basename(output_filepath),
                        mime="text/csv"
                    )

            else:
                st.warning("No results available")


if __name__ == "__main__":
    main()