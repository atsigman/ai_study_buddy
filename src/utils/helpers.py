"""
Quiz management-related utility methods.
Called in the main (application) module.
"""

import pandas as pd
import streamlit as st

from pathlib import Path
from typing import Literal

from src.generator.question_generator import QuestionGenerator


def rerun():
    """
    Enable session to rerun.
    """
    st.session_state["rerun_trigger"] = not st.session_state.get("rerun_trigger", False)


class QuizManager:
    def __init__(self):
        self.questions = []
        self.user_answers = []
        self.results = []

    def generate_questions(
        self,
        generator: QuestionGenerator,
        topic: str,
        question_type: Literal["Multiple Choice", "Fill in the Blank"],
        difficulty: str,
        n_questions: int,
    ) -> bool:
        """
        Generate and cache all questions.
        """

        # clear all previous data:
        self.questions = []
        self.user_answers = []
        self.results = []

        try:
            for _ in range(n_questions):
                if question_type == "Multiple Choice":

                    question = generator.generate_mcq(topic, difficulty.lower(), self.questions)

                    self.questions.append(
                        {
                            "type": "MCQ",
                            "question": question.question,
                            "options": question.options,
                            "correct_answer": question.correct_answer,
                        }
                    )
                else:
                    question = generator.generate_fill_blank_question(
                        topic, difficulty.lower(), self.questions
                    )

                    self.questions.append(
                        {
                            "type": "Fill in the blank",
                            "question": question.question,
                            "correct_answer": question.correct_answer,
                        }
                    )
        except Exception as e:
            st.error(f"Error generating question: {str(e)}")
            return False

        return True

    def attempt_quiz(self) -> None:
        """
        Create GUI object for each question. Cache
        user responses.
        """
        # Because responses may be user-modified during a session,
        # store in a dict:
        if "answers" not in st.session_state:
            st.session_state.answers = {}  # key: question index, value: current answer

        for i, q in enumerate(self.questions):
            st.markdown(f"**Question {i + 1}: {q['question']}**")

            if q["type"] == "MCQ":
                user_answer = st.radio(
                    f"Select an answer for Question {i + 1}",
                    q["options"],
                    key=f"mcq_{i}",
                )

            else:
                user_answer = st.text_input(
                    f"Fill in the blank for Question {i + 1}", key=f"fill_blank_{i}"
                )

            if user_answer:
                st.session_state.answers[i] = user_answer

        self.user_answers = [
            st.session_state.answers[i]
            for i in range(len(self.questions))
            if i in st.session_state.answers
        ]

    def evaluate_quiz(self) -> None:
        """
        Compare user and correct answers to each question.
        Set is_correct value accordingly.
        """
        self.results = []

        for i, (q, user_answer) in enumerate(zip(self.questions, self.user_answers)):
            result_dict = {
                "question_number": i + 1,
                "question": q["question"],
                "question_type": q["type"],
                "user_answer": user_answer,
                "correct_answer": q["correct_answer"],
                "is_correct": False,
            }

            if q["type"] == "MCQ":
                result_dict["options"] = q["options"]

            else:
                result_dict["options"] = []
                user_answer = user_answer.strip().lower()
                q["correct_answer"] = q["correct_answer"].lower()

            result_dict["is_correct"] = user_answer == q["correct_answer"]

            self.results.append(result_dict)

    def generate_result_dataframe(self) -> pd.DataFrame:
        """
        Wrap current results in a DataFrame.
        """
        if not self.results:
            return pd.DataFrame()

        return pd.DataFrame(self.results)

    def save_to_csv(self, filename_prefix="quiz_results") -> str:
        """
        Save current quiz results to a CSV.
        """
        if not self.results:
            st.warning("No quiz results to save!!")
            return None

        df = self.generate_result_dataframe()

        # format output path:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{filename_prefix}_{timestamp}.csv"

        output_dir = "results"
        Path(output_dir).mkdir(exist_ok=True, parents=True)
        output_path = str(Path(output_dir, output_filename))

        try:
            df.to_csv(output_path, index=False)
            st.success(f"Results saved to {output_path}")
            return output_path

        except Exception as e:
            st.error(f"Failed to save results: {e}")
            return None
