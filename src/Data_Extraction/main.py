"""Main script to run the entire pipeline."""

import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from scraping.financial_source_finder import FinancialSourcesFinder
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("financial_sources_finder.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    """Run the financial sources finder."""
    import argparse

    parser = argparse.ArgumentParser(description="Find financial sources for multinational companies")
    parser.add_argument("--input", default="dataset/extraction.csv", help="Input CSV file with a list of companies")
    parser.add_argument("--output", default="financial_sources_results.csv", help="Output CSV file")
    parser.add_argument("--source-type", default="Annual Report", help="Type of financial source to search for")
    parser.add_argument("--api-key", help="Gemini API key (optional if set as an environment variable)")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads for parallel processing")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for processing")
    parser.add_argument("--validation-threshold", type=int, default=80, help="Validation threshold (0-100)")
    parser.add_argument("--max-tuning", type=int, default=3, help="Maximum number of tuning iterations")

    args = parser.parse_args()

    # Configure the API key if provided
    env_path = Path("src/Data_extraction/config/model_config") / ".env"
    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("Gemini API key not provided. Set GOOGLE_API_KEY or use --api-key, if not created go to the official website: https://aistudio.google.com/apikey")
        sys.exit(1)

    df = pd.read_csv(args.input, sep=";")

    # Initialize the finder
    finder = FinancialSourcesFinder(api_key=api_key, max_tuning_iterations=args.max_tuning, validation_threshold=args.validation_threshold)

    for row in tqdm(df.itertuples()):
        company_name = row.NAME
        variable = row.VARIABLE
        logger.info("Processing company: %s for the variable: %s", company_name, variable)

        # Find the official website of the company
        
        url, year, confidence, source_description, page_status = finder.find_financial_source(company_name, variable)
        df.at[row.Index, "VALUE"] = url
        df.at[row.Index, "CURRENCY"] = None 
        df.at[row.Index, "REFYEAR"] = year


if __name__ == "__main__":
    main()
