"""Prompt Tuner Module."""

import logging
import secrets
import sys
import time

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from google.generativeai.types import generation_types
from prompts.base_prompt import base_prompt_improving
from prompts.prompt_improving import improve_prompt
from utils import load_config_yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("financial_sources_finder.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class PromptTuner:
    """Module for automatic prompt optimization based on feedback."""

    def __init__(self, initial_prompt_template: str | None = None):
        """Initialize the PromptTuner with a default prompt template.

        Args:
            initial_prompt_template (str): Template for the initial prompt.
        """
        self.current_prompt = initial_prompt_template or base_prompt_improving
        self.config = load_config_yaml("src/Data_Extraction/config/model_config/config.yaml")

        self.tuning_history: list = []
        self.max_retries = self.config["max_retries"]
        self.models_name = self.config["models_name"]

    def inizialize_model(self):
        """Initialize the generative model for prompt tuning."""
        self.selected_model_name = secrets.choice(self.models_name)
        logger.info("Selected model: %s", self.selected_model_name)
        self.model = genai.GenerativeModel(self.selected_model_name)

    def generate_prompt(self, company_name: str, source_type: str) -> str:
        """
        Generate the full prompt for the given company and source type.

        Args:
            company_name (str): Company name
            source_type (str): Type of financial source

        Returns
        -------
            str: The full prompt with the company name and source type filled in
        """
        return self.current_prompt.format(company_name=company_name, source_type=source_type)

    def improve_prompt(self, report_url, company_name):
        """Improves the current prompt using feedback from Gemini.

        Args:
            company_name (str): Name of the company
            source_type (str): Type of financial source
            scraping_result (dict): Result of the web scraping
            validation_result (dict): Result of the validation

        Returns
        -------
            str: New improved prompt
        """
        # Improves the current prompt using feedback from Gemini
        return improve_prompt.format(report_url=report_url, company_name=company_name)

    def call(self, prompt: str) -> generation_types.GenerateContentResponse | None:
        """Call the model with the given prompt and handle retries for quota errors."""
        retries = 0
        self.inizialize_model()
        while retries < self.max_retries:
            response = None
            try:
                response = self.model.generate_content(prompt)
            except ResourceExhausted as e:
                logger.warning("Quota exceeded: %s", e.message)
                # Try to extract retry delay from exception, or default to 60 seconds
                delay = getattr(e, "retry_delay", 60)
                delay = delay.seconds if hasattr(delay, "seconds") else 60
                logger.info("Retrying in %d seconds... (attempt %d of %d)", delay, retries + 1, self.max_retries)
                time.sleep(delay)
            except Exception as e:
                logger.exception("Unhandled exception during model call: %s", e)  # noqa: TRY401
                break  # Or re-raise depending on your error handling policy

            if response:
                logger.info("Response received successfully.")
                return response

            retries += 1

        logger.error("Failed to get a response after %d retries.", self.max_retries)
        return None
