"""Data preparation and submission module for the Data Discovery project."""

import logging
import os
from pathlib import Path
import re
import json

import pandas as pd
from utils import load_config_yaml, load_json_obj

CONFIDENCE_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def normalize_name(name):
    """Normalize company names to enable matching."""
    return re.sub(r'\W+', '', str(name)).upper()


def is_valid_url(url):
    """Check if a string is a valid URL format."""
    if pd.isna(url) or url == '' or url == 'N/A':
        return False
    
    # Check for common invalid formats
    if url == 'NO_DATA_FOUND':
        return False
    
    # Check if it's a dictionary-like string
    if isinstance(url, str) and (url.startswith('{') or url.startswith('{')):
        return False
    
    # Basic URL validation
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(url_pattern, str(url)))


def clean_src_column(src_value):
    """Clean and validate SRC column values."""
    if pd.isna(src_value) or src_value == '':
        return ''
    
    src_str = str(src_value).strip()
    
    # Handle common invalid formats
    if src_str == 'NO_DATA_FOUND':
        return ''
    
    # Handle dictionary-like strings
    if src_str.startswith('{') and src_str.endswith('}'):
        try:
            # Try to parse as JSON and extract URL
            data = json.loads(src_str.replace("'", '"'))
            if isinstance(data, dict) and 'url' in data:
                url = data['url']
                if is_valid_url(url):
                    return url
        except (json.JSONDecodeError, ValueError):
            pass
        return ''
    
    # Validate as URL
    if is_valid_url(src_str):
        return src_str
    
    return ''


def clean_refyear_column(refyear_value):
    """Clean and validate REFYEAR column values to ensure they are numeric."""
    if pd.isna(refyear_value) or refyear_value == '' or refyear_value == 'N/A':
        return None
    
    # Convert to string first to handle various input types
    refyear_str = str(refyear_value).strip()
    
    # Handle common invalid formats
    if refyear_str in ['NO_DATA_FOUND', 'N/A', '', 'nan', 'None']:
        return None
    
    # Handle dictionary-like strings
    if refyear_str.startswith('{') and refyear_str.endswith('}'):
        try:
            # Try to parse as JSON and extract year
            data = json.loads(refyear_str.replace("'", '"'))
            if isinstance(data, dict) and 'year' in data:
                year_val = data['year']
                if year_val and str(year_val).strip():
                    return clean_refyear_column(year_val)
        except (json.JSONDecodeError, ValueError):
            pass
        return None
    
    # Try to extract numeric value
    try:
        # Remove any non-digit characters except decimal point and minus sign
        cleaned = re.sub(r'[^\d.-]', '', refyear_str)
        if cleaned:
            # Convert to float first, then to int if it's a whole number
            float_val = float(cleaned)
            if float_val.is_integer() and 1800 <= float_val <= 2030:  # Reasonable year range
                return int(float_val)
            elif 1800 <= float_val <= 2030:
                return int(float_val)  # Round to nearest integer
    except (ValueError, TypeError):
        pass
    
    return None


class DataExtractionSubmission:
    """Handles data preparation and submission for the Data Discovery project."""

    def __init__(self):
        self.config = load_config_yaml("src/Data_Extraction/config/submission_config/config.yaml")
        self.original_data_path = self.config.get("original_data_path")
        self.reports_path = self.config.get("reports_path")
        self.submission_path = self.config.get("submission_path")
        self.dataset = pd.read_csv(self.original_data_path, sep=";")
        self.processed_data = None
        self.logger = logging.getLogger(__name__)

    def load_reports_data(self):
        """Load all report JSON files and combine them into a single dataframe."""
        all_reports = []

        if not os.path.exists(self.reports_path):
            self.logger.error(f"Reports path does not exist: {self.reports_path}")
            return pd.DataFrame()

        json_files = list(Path(self.reports_path).glob("*.json"))

        if not json_files:
            self.logger.warning(f"No JSON files found in {self.reports_path}")
            return pd.DataFrame()

        for json_file in json_files:
            try:
                reports = load_json_obj(str(json_file))
                if isinstance(reports, list):
                    all_reports.extend(reports)
                else:
                    all_reports.append(reports)
            except Exception as e:
                self.logger.error(f"Error loading {json_file}: {e}")
                continue

        if not all_reports:
            self.logger.warning("No valid reports found")
            return pd.DataFrame()

        return pd.DataFrame(all_reports)

    def merge_with_original_data(self, reports_df):
        """Populate original dataset columns with data from reports."""
        result_df = self.dataset.copy()

        if reports_df.empty:
            self.logger.warning("Reports dataframe is empty, returning original dataset")
            return result_df

        # Create lookup from normalized report keys
        reports_lookup = {}
        for _, row in reports_df.iterrows():
            key = (row['ID'], normalize_name(row['NAME']), str(row['VARIABLE']).upper())
            reports_lookup[key] = {
                'VALUE': row.get('VALUE'),
                'CURRENCY': row.get('CURRENCY'),
                'REFYEAR': row.get('REFYEAR'),
                'SRC': row.get('SRC')
            }

        for idx, row in result_df.iterrows():
            key = (row['ID'], normalize_name(row['NAME']), str(row['VARIABLE']).upper())
            if key in reports_lookup:
                report_data = reports_lookup[key]
                for col in ['VALUE', 'CURRENCY', 'REFYEAR', 'SRC']:
                    if pd.isna(row[col]) or row[col] in ['', 'N/A']:
                        if pd.notna(report_data.get(col)) and report_data[col] != '':
                            result_df.at[idx, col] = report_data[col]

        return result_df

    def add_quality_metrics(self, df, reports_df):
        """Add quality and confidence metrics to the dataframe."""
        df = df.copy()

        df['DATA_COMPLETENESS'] = 0.0
        df['CONFIDENCE_LEVEL'] = 'LOW'
        df['PAGE_STATUS'] = 'Unknown'
        df['HAS_SOURCE'] = False

        if not reports_df.empty and 'Page Status' in reports_df.columns:
            page_status_map = {
                (row['ID'], normalize_name(row['NAME']), str(row['VARIABLE']).upper()): row['Page Status']
                for _, row in reports_df.iterrows()
            }

            for idx, row in df.iterrows():
                key = (row['ID'], normalize_name(row['NAME']), str(row['VARIABLE']).upper())
                if key in page_status_map:
                    df.at[idx, 'PAGE_STATUS'] = page_status_map[key]

        for idx, row in df.iterrows():
            completeness_score = 0
            confidence = 'LOW'

            if pd.notna(row['VALUE']) and row['VALUE'] != '':
                completeness_score += 0.4
                confidence = 'MEDIUM'

            if pd.notna(row['SRC']) and row['SRC'] != '':
                completeness_score += 0.3
                df.at[idx, 'HAS_SOURCE'] = True
                if confidence == 'MEDIUM':
                    confidence = 'HIGH'

            if pd.notna(row['CURRENCY']) and row['CURRENCY'] != '':
                completeness_score += 0.15

            if pd.notna(row['REFYEAR']) and row['REFYEAR'] != '':
                completeness_score += 0.15

            if row['PAGE_STATUS'] == 'Page found':
                completeness_score += 0.1
                if completeness_score >= 0.7:
                    confidence = 'HIGH'

            df.at[idx, 'DATA_COMPLETENESS'] = min(completeness_score, 1.0)
            df.at[idx, 'CONFIDENCE_LEVEL'] = confidence

        return df

    def clean_submission_data(self, df):
        """Clean and validate data before submission."""
        df = df.copy()
        
        # Clean SRC column
        df['SRC'] = df['SRC'].apply(clean_src_column)
        
        # Clean REFYEAR column
        df['REFYEAR'] = df['REFYEAR'].apply(clean_refyear_column)
        
        # Update HAS_SOURCE based on cleaned SRC
        df['HAS_SOURCE'] = df['SRC'].apply(lambda x: bool(x and x.strip()))
        
        # Recalculate confidence levels based on cleaned data
        for idx, row in df.iterrows():
            completeness_score = 0
            confidence = 'LOW'
            
            if pd.notna(row['VALUE']) and row['VALUE'] != '':
                completeness_score += 0.4
                confidence = 'MEDIUM'
            
            if row['HAS_SOURCE']:
                completeness_score += 0.3
                if confidence == 'MEDIUM':
                    confidence = 'HIGH'
            
            if pd.notna(row['CURRENCY']) and row['CURRENCY'] != '':
                completeness_score += 0.15
            
            if pd.notna(row['REFYEAR']) and row['REFYEAR'] != '':
                completeness_score += 0.15
            
            if row['PAGE_STATUS'] == 'Page found':
                completeness_score += 0.1
                if completeness_score >= 0.7:
                    confidence = 'HIGH'
            
            df.at[idx, 'DATA_COMPLETENESS'] = min(completeness_score, 1.0)
            df.at[idx, 'CONFIDENCE_LEVEL'] = confidence
        
        return df

    def generate_summary_statistics(self, df):
        """Generate summary statistics for the processed data."""
        summary = {
            'total_records': len(df),
            'unique_companies': df['ID'].nunique(),
            'variables_coverage': df.groupby('VARIABLE').agg({
                'VALUE': lambda x: (pd.notna(x) & (x != '')).sum(),
                'ID': 'count'
            }).rename(columns={'VALUE': 'filled_count', 'ID': 'total_count'}),
            'confidence_distribution': df['CONFIDENCE_LEVEL'].value_counts(),
            'page_status_distribution': df['PAGE_STATUS'].value_counts(),
            'average_completeness': df['DATA_COMPLETENESS'].mean(),
            'companies_with_sources': df[df['HAS_SOURCE']]['ID'].nunique(),
            'invalid_urls_cleaned': 0  # Will be updated during cleaning
        }

        summary['variables_coverage']['coverage_percentage'] = (
            summary['variables_coverage']['filled_count'] /
            summary['variables_coverage']['total_count'] * 100
        ).round(2)

        return summary

    def populate_dataframe(self):
        """Main method to populate the dataframe with processed data."""
        self.logger.info("Starting data population process...")

        reports_df = self.load_reports_data()
        self.logger.info(f"Loaded {len(reports_df)} report records")

        merged_df = self.merge_with_original_data(reports_df)
        self.logger.info(f"Merged data contains {len(merged_df)} records")

        processed_df = self.add_quality_metrics(merged_df, reports_df)
        
        # Clean the data before final processing
        cleaned_df = self.clean_submission_data(processed_df)
        
        self.processed_data = cleaned_df

        summary = self.generate_summary_statistics(cleaned_df)
        self.logger.info(f"Data processing complete. Coverage: {summary['average_completeness']:.2%}")

        return cleaned_df, summary

    def save_submission_data(self, output_filename=None):
        """Save the processed data to submission format."""
        if self.processed_data is None:
            self.logger.error("No processed data available. Run populate_dataframe() first.")
            return False

        if output_filename is None:
            output_filename = "data_discovery_submission.csv"

        output_path = os.path.join(self.submission_path, output_filename)
        os.makedirs(self.submission_path, exist_ok=True)

        try:
            submission_columns = ['ID', 'NAME', 'VARIABLE', 'SRC', 'VALUE', 'CURRENCY', 'REFYEAR']
            submission_df = self.processed_data[submission_columns].copy()
            
            # Final validation: ensure no invalid URLs or non-numeric REFYEAR values in submission
            invalid_urls = []
            invalid_years = []
            
            for idx, row in submission_df.iterrows():
                # Check SRC column
                if row['SRC'] and not is_valid_url(row['SRC']):
                    invalid_urls.append(f"ID: {row['ID']}, SRC: {row['SRC']}")
                    submission_df.at[idx, 'SRC'] = ''  # Clear invalid URLs
                
                # Check REFYEAR column
                if pd.notna(row['REFYEAR']):
                    try:
                        # Ensure it's a valid number
                        year_val = float(row['REFYEAR'])
                        if not (1800 <= year_val <= 2030):  # Reasonable year range
                            invalid_years.append(f"ID: {row['ID']}, REFYEAR: {row['REFYEAR']}")
                            submission_df.at[idx, 'REFYEAR'] = None
                    except (ValueError, TypeError):
                        invalid_years.append(f"ID: {row['ID']}, REFYEAR: {row['REFYEAR']}")
                        submission_df.at[idx, 'REFYEAR'] = None
            
            if invalid_urls:
                self.logger.warning(f"Cleared {len(invalid_urls)} invalid URLs from submission data")
            
            if invalid_years:
                self.logger.warning(f"Cleared {len(invalid_years)} invalid REFYEAR values from submission data")
            
            submission_df.to_csv(output_path, sep=';', index=False)

            detailed_path = output_path.replace('.csv', '_detailed.csv')
            self.processed_data.to_csv(detailed_path, sep=';', index=False)

            self.logger.info(f"Submission data saved to {output_path}")
            self.logger.info(f"Detailed data saved to {detailed_path}")

            return True
        except Exception as e:
            self.logger.error(f"Error saving submission data: {e}")
            return False

    def get_company_data(self, company_id):
        """Get all data for a specific company."""
        if self.processed_data is None:
            self.logger.error("No processed data available.")
            return pd.DataFrame()
        return self.processed_data[self.processed_data['ID'] == company_id].copy()

    def get_variable_summary(self, variable_name):
        """Get summary for a specific variable across all companies."""
        if self.processed_data is None:
            self.logger.error("No processed data available.")
            return pd.DataFrame()
        return self.processed_data[self.processed_data['VARIABLE'] == variable_name].copy()

    def run(self, save_output=True, output_filename=None, verbose=True):
        """Main execution method that runs the complete data processing pipeline."""
        try:
            if verbose:
                print("=" * 60)
                print("DATA DISCOVERY - SUBMISSION PROCESSING")
                print("=" * 60)
                print(f"Original dataset: {len(self.dataset)} records")
                print(f"Reports path: {self.reports_path}")
                print(f"Submission path: {self.submission_path}")
                print("-" * 60)

            if verbose:
                print("Step 1: Loading and processing data...")

            processed_df, summary = self.populate_dataframe()

            if verbose:
                print(f"✓ Processed {len(processed_df)} records")
                print(f"✓ Coverage: {summary['unique_companies']} companies")
                print(f"✓ Average completeness: {summary['average_completeness']:.1%}\n")
                print("Variable Coverage:")
                for var, stats in summary['variables_coverage'].iterrows():
                    print(f"  {var}: {stats['filled_count']}/{stats['total_count']} "
                          f"({stats['coverage_percentage']:.1f}%)")
                print("\nConfidence Distribution:")
                for conf, count in summary['confidence_distribution'].items():
                    percentage = (count / len(processed_df)) * 100
                    print(f"  {conf}: {count} records ({percentage:.1f}%)")
                print("\nPage Access Status:")
                for status, count in summary['page_status_distribution'].items():
                    percentage = (count / len(processed_df)) * 100
                    print(f"  {status}: {count} records ({percentage:.1f}%)\n")

            if save_output:
                if verbose:
                    print("Step 2: Saving output files...")
                success = self.save_submission_data(output_filename)
                if success and verbose:
                    print("✓ Files saved successfully")
                elif not success:
                    print("✗ Error saving files")
                    return processed_df, summary, False

            if verbose:
                print("-" * 60)
                print("PROCESSING COMPLETE")
                print(f"✓ {summary['companies_with_sources']} companies have source URLs")
                print(f"✓ {summary['confidence_distribution'].get('HIGH', 0)} high-confidence records")
                print(f"✓ {summary['confidence_distribution'].get('MEDIUM', 0)} medium-confidence records")
                low_conf = summary['confidence_distribution'].get('LOW', 0)
                if low_conf > 0:
                    print(f"⚠ {low_conf} low-confidence records need attention")
                not_found = summary['page_status_distribution'].get('Page not found', 0)
                if not_found > 0:
                    print(f"⚠ {not_found} records with inaccessible pages")
                print("=" * 60)

            return processed_df, summary, True

        except Exception as e:
            error_msg = f"Error in run method: {str(e)}"
            self.logger.error(error_msg)
            if verbose:
                print(f"✗ {error_msg}")
            return pd.DataFrame(), {}, False