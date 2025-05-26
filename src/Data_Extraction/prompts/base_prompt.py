"""Base prompt for financial data discovery tasks."""

base_prompt_improving = -""" YOU ARE A SENIOR FINANCIAL RESEARCH EXPERT with extensive experience in locating and verifying official sources of financial data for multinational corporations.

TASK: For the Multinational Enterprise (MNE) group with the following details:
- ID: {{ID}}
- NAME: {{NAME}}
- VARIABLE of interest: {{VARIABLE}}

Identify and provide the most authoritative, specific, and up-to-date source of financial data for this company, focused on the requested document type: {{source_type}} (e.g., annual report, quarterly earnings, sustainability report).

DETAILED INSTRUCTIONS:
1. Confirm the official corporate website of the company by verifying domain authenticity (e.g., corporate suffix, known trademarks).
2. Navigate to the "Investor Relations" section or its closest equivalent (e.g., "Financial Reports", "SEC Filings").
3. Locate the most recent official document matching the requested source_type.
4. Ensure the document is published by the company, not a third party (avoid summaries, media outlets).
5. Extract the direct URL to the document—preferably in downloadable PDF or equivalent format.
6. Confirm the document is freely accessible (no login, subscription, or paywall required).
7. Extract the VALUE of the specified VARIABLE.
8. Identify the CURRENCY (if applicable).
9. Determine the REFERENCE YEAR (REFYEAR) of the report based on fiscal year or publication metadata.
10. Assess your confidence level in the reliability of the source.

OUTPUT FORMAT (strict JSON):
{{
  "ID": "{{ID}}",
  "NAME": "{{NAME}}",
  "VARIABLE": "{{VARIABLE}}",
  "VALUE": "Extracted financial value as found in the document",
  "CURRENCY": "Currency in which the value is reported, if applicable",
  "REFYEAR": "Fiscal year of the data (format: YYYY)",
  "SRC": "Direct URL to the official financial document (PDF or equivalent)",
  "confidence": "HIGH / MEDIUM / LOW",
  "notes": "Concise rationale explaining your source selection and any relevant observations"
}}

IMPORTANT NOTES:
- Prioritize documents hosted directly on the official corporate domain.
- Avoid URLs requiring authentication or redirecting to unverified domains.
- If the exact source_type or VARIABLE is unavailable, clearly indicate this and provide the closest verified equivalent.
- Maintain professional tone, source accuracy, and data integrity.
"""  # noqa: E501

base_prompt_template = """
YOU ARE A FINANCIAL RESEARCH EXPERT specializing in locating authoritative and official financial data sources for multinational companies.

TASK: Identify the most authoritative, specific, and up-to-date financial data source for "{company_name}" (requested source type: {source_type}).

INSTRUCTIONS:

1. URL SELECTION
- Provide the MOST SPECIFIC URL directly linking to the page or document containing the latest financial data.
- Avoid generic URLs such as the company homepage or broad IR landing pages.
- Prioritize URLs pointing to specific financial statements, reports, or filings over general pages.
- Prefer official Investor Relations (IR) pages over aggregators or search engines.
- For U.S. companies, SEC filings (10-K, 10-Q) are IDEAL; for EU companies, ESEF/XBRL reports are preferred.
- PDF or XBRL documents are HIGHLY PREFERRED over HTML pages.

2. REFERENCE YEAR
- Identify the fiscal/reporting year of the financial data, NOT the publication year.
- Choose the MOST RECENT period available (annual or quarterly).
- Use numeric year format, e.g., "2023" or "2023-2024".

3. SOURCE PRIORITY (based on {source_type}):

- Annual Report: IR website > SEC filings > official PDFs > financial databases
- Consolidated: official consolidated documents > IR website > financial databases
- Quarterly: official quarterly reports > IR website > financial databases
- Other types: IR website > official documents > reliable financial databases

4. PRIORITIZATION OVERALL:
Official IR page > Specific document/report > Financial database > Aggregator

5. CONFIDENCE ASSESSMENT
- HIGH: Direct official documents/reports from IR or regulator with clear recent fiscal year.
- MEDIUM: Reliable financial databases or aggregated sources with recent data.
- LOW: Indirect, outdated, or generic sources.

RESPONSE FORMAT:

Return a JSON object ONLY, with EXACT fields and no extra text or commentary:

{{
    "url": "EXACT_SOURCE_URL",
    "year": "REFERENCE_YEAR",
    "confidence": "HIGH/MEDIUM/LOW",
    "source_type": "{source_type}"
}}

{optimization_instructions}

IMPORTANT: If multiple sources are found, select ONLY the best one according to the above criteria. Accuracy and relevance are critical.
"""
web_scraping_prompt = """
ROLE:
You are a SENIOR FINANCIAL DATA ANALYST and TECHNICAL WEB SCRAPING ENGINEER. Your expertise lies in locating, extracting, and verifying official financial and corporate information for multinational enterprise (MNE) groups. Your task supports the compilation of structured datasets for global MNE analysis.

OBJECTIVE:
Develop a Python script to identify and extract the most reliable, specific, and up-to-date financial and corporate data source for the MNE group: "{company_name}", targeting the variable: "{variable}".

VARIABLES TO EXTRACT:
Each company entry includes one of the following VARIABLE types, and your script should find the best available source and reference year:

1. Country of headquarters (in ISO 3166-1 alpha-2 format)
2. Number of employees (global, annual)
3. Net turnover (annual, full integer)
4. Total assets (annual, full integer)
5. Company website (official domain)
6. Main activity based on original NACE Rev. 2 (3-character code or shorter)

TASK DESCRIPTION:
Write a production-ready Python script that:
- Searches and identifies the most specific, official source (e.g., investor relations, financial reports, company registries, Wikipedia infoboxes, or news databases)
- Extracts the appropriate value depending on the VARIABLE
- Extracts and returns:
  - the data value (VALUE)
  - the source URL (SRC)
  - the currency (CURRENCY), if applicable
  - the reference year (REFYEAR), if applicable

🧠 INTELLIGENCE AND STRUCTURE:
- Use BeautifulSoup for HTML parsing
- Use requests with a 5-second timeout
- Prioritize:
  - Official IR websites
  - Government or regulatory filings (e.g. SEC EDGAR, national registries)
  - Wikipedia (for country, website, NACE code)
  - Trusted financial databases (as fallback)

📦 OUTPUT FORMAT:
The script must return a Python dictionary as:

{
    "url": "EXACT_SOURCE_URL",       # Direct page where the data was extracted
    "value": "EXTRACTED_VALUE",      # Must match expected data format (e.g. ISO country code, integer, NACE code, URL, etc.)
    "currency": "ISO4217_CODE",      # Currency (only for financial values), otherwise empty string
    "year": "REFERENCE_YEAR",        # Reporting year or year of data, otherwise empty string
    "confidence": "HIGH/MEDIUM/LOW"  # Confidence level
}

🔒 CONSTRAINTS:
- DO NOT use paid APIs, headless browsers, or automation tools (e.g. Selenium)
- Use only publicly accessible and reliable sources
- Ensure:
  - Clean, modular code with inline comments
  - Robust exception handling
  - Accuracy, traceability, and timeliness of data

🚀 EXECUTION REQUIREMENT:
The script must run directly via:

if __name__ == "__main__":
    result = main()

Save the final dictionary output in the variable named `result`.

📌 EXAMPLES OF ACCEPTABLE SOURCES:
- Investor Relations page with 2023 Annual Report (PDF preferred)
- Company registry with financial data
- Wikipedia page infobox for country, website, or employee count
- SEC or equivalent filings
- Bloomberg or Reuters for fallback (if official unavailable)

🎯 PRIORITY:
Always prefer: Official IR page > Government registry > Specific financial document > Wikipedia/aggregator

"""
