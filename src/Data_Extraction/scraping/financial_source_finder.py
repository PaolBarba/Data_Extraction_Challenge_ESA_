"""Main module for the Financial Sources Finder project."""

import json
import logging
import os
import sys
from pathlib import Path
from time import time
from typing import Any

import google.generativeai as genai
from scraping.scraping_challenge import WebScraperModule
from tqdm import tqdm
from utils import save_json_obj

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("financial_sources_finder.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class FinancialSourcesFinder:
    """Classe principale che coordina il processo di ricerca delle fonti finanziarie."""

    def __init__(self, api_key: str | None = None, max_tuning_iterations: int = 3, validation_threshold: int = 80):
        """
        Initialize the finder with the necessary configurations.

        Args:
            api_key (str): API key for Gemini (optional if already configured)
            max_tuning_iterations (int): Maximum number of tuning iterations
            validation_threshold (int): Validation threshold (0-100)
        """
        if api_key:
            genai.configure(api_key=api_key)

        self.scraper = WebScraperModule()
        self.max_tuning_iterations = max_tuning_iterations
        self.validation_threshold = validation_threshold

    def _load_existing_report(self, report_path: Path) -> dict[str, Any]:
        """
        Load an existing report from the specified path.

        Args:
            report_path (Path): Path to the report file.

        Returns
        -------
            dict: Loaded report data.
        """
        with report_path.open("r") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]  # Wrap single dict into a list
            except json.JSONDecodeError:
                data = []
        return data

    def find_financial_source(self, company_name: str, variable: str) -> dict[str, Any]:
        """
        Find the financial source for a company with automatic tuning.

        Args:
            company_name (str): Name of the company.
            source_type (str): Type of financial source.

        Returns
        -------
            dict: Final result with URL, yaear, and metadata.
        """
        url, value, currency, refyear, page_status = self.scraper.scrape_financial_sources(company_name, variable)


        return url, value, currency, refyear, page_status
