from langchain_core.output_parsers.pydantic import PydanticOutputParser

from src.models.question_schemas import MCQuestion, FillBlankQuestion
from src.prompts.templates import mcq_prompt_template, fill_blank_prompt_template
from src.llm.groq_client import get_groq_llm
from src.config.settings import settings
from src.common.custom_exception import CustomException
from src.common.logger import get_logger


class QuestionGenerator:
    def __init__(self):
        self.llm = get_groq_llm()
        self.logger = get_logger(self.__class__.__name__)

    def _retry_and_parse(
        self, prompt: str, parser: PydanticOutputParser, topic: str, difficulty: str
    ):
        """
        Attempt to parse the returned question.
        """
        for attempt in range(settings.MAX_RETRIES):
            try:
                self.logger.info(
                    f"Generating question for topic {topic} with difficulty {difficulty}..."
                )
                response = self.llm.invoke(
                    prompt.format(topic=topic, difficulty=difficulty)
                )
                parsed = parser.parse(response.content)
                self.logger.info("Successfully parsed the question")
                return parsed

            except Exception as e:
                self.logger.error(f"Error: {str(e)}")
                if attempt == settings.MAX_RETRIES - 1:
                    raise CustomException(
                        f"Generation failed after {attempt + 1} retries", e
                    )

    def generate_mcq(self, topic: str, difficulty: str = "medium") -> MCQuestion:
        try:
            parser = PydanticOutputParser(pydantic_object=MCQuestion)
            question = self._retry_and_parse(
                mcq_prompt_template, parser, topic, difficulty
            )

            if (
                len(question.options) != 4
                and question.correct_answer not in question.options
            ):
                raise ValueError("Invalid MCQ structure")

            self.logger.info("Generated a valid MCQ")
            return question

        except Exception as e:
            self.logger.error(f"Failed to generate MCQ: {str(e)}")
            raise CustomException("MCQ generation failed", e)

    def generate_fill_blank_question(
        self, topic: str, difficulty: str = "medium"
    ) -> FillBlankQuestion:
        try:
            parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)
            question = self._retry_and_parse(
                fill_blank_prompt_template, parser, topic, difficulty
            )

            if "__" not in question.question:
                raise ValueError("Fill in blanks should contain '__'")

            self.logger.info("Generated a valid FillBlankQuestion")
            return question

        except Exception as e:
            self.logger.error(f"Failed to generate FillBlankQuestion: {str(e)}")
            raise CustomException("FillBlankQuestion generation failed", e)
