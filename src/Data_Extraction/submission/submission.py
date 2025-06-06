"""Data preparation and submission module for the Data Discovery project."""

import logging
import os
from pathlib import Path

import pandas as pd
from utils import load_config_yaml, load_json_obj

CONFIDENCE_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


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
        
        # Get all JSON files from reports directory
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
        
        # Convert to DataFrame
        reports_df = pd.DataFrame(all_reports)
        return reports_df

    def merge_with_original_data(self, reports_df):
        """Populate original dataset columns with data from reports."""
        # Start with a copy of the original dataset to preserve exact structure
        result_df = self.dataset.copy()
        
        if reports_df.empty:
            self.logger.warning("Reports dataframe is empty, returning original dataset")
            return result_df
        
        # Create a lookup dictionary for efficient matching
        reports_lookup = {}
        for _, row in reports_df.iterrows():
            key = (row['ID'], row['NAME'], row['VARIABLE'])
            reports_lookup[key] = {
                'VALUE': row.get('VALUE'),
                'CURRENCY': row.get('CURRENCY'),
                'REFYEAR': row.get('REFYEAR'),
                'SRC': row.get('SRC')
            }
        
        # Populate the original dataset row by row
        for idx, row in result_df.iterrows():
            key = (row['ID'], row['NAME'], row['VARIABLE'])
            
            if key in reports_lookup:
                report_data = reports_lookup[key]
                
                # Only update if report has non-null values and original is empty/null
                for col in ['VALUE', 'CURRENCY', 'REFYEAR', 'SRC']:
                    if (pd.isna(result_df.at[idx, col]) or result_df.at[idx, col] == '' or result_df.at[idx, col] == 'N/A'):
                        if pd.notna(report_data[col]) and report_data[col] != '':
                            result_df.at[idx, col] = report_data[col]
        
        return result_df

    def add_quality_metrics(self, df, reports_df):
        """Add quality and confidence metrics to the dataframe."""
        df = df.copy()
        
        # Initialize quality columns
        df['DATA_COMPLETENESS'] = 0.0
        df['CONFIDENCE_LEVEL'] = 'LOW'
        df['PAGE_STATUS'] = 'Unknown'
        df['HAS_SOURCE'] = False
        
        if not reports_df.empty and 'Page Status' in reports_df.columns:
            # Map page status from reports
            page_status_map = reports_df.set_index(['ID', 'NAME', 'VARIABLE'])['Page Status'].to_dict()
            
            for idx, row in df.iterrows():
                key = (row['ID'], row['NAME'], row['VARIABLE'])
                if key in page_status_map:
                    df.at[idx, 'PAGE_STATUS'] = page_status_map[key]
        
        # Calculate data completeness and confidence for each row
        for idx, row in df.iterrows():
            completeness_score = 0
            confidence = 'LOW'
            
            # Check if key fields are filled
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
            
            # Bonus for successful page access
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
            'companies_with_sources': df[df['HAS_SOURCE']]['ID'].nunique()
        }
        
        # Calculate coverage percentages
        summary['variables_coverage']['coverage_percentage'] = (
            summary['variables_coverage']['filled_count'] / 
            summary['variables_coverage']['total_count'] * 100
        ).round(2)
        
        return summary

    def populate_dataframe(self):
        """Main method to populate the dataframe with processed data."""
        self.logger.info("Starting data population process...")
        
        # Load reports data
        reports_df = self.load_reports_data()
        self.logger.info(f"Loaded {len(reports_df)} report records")
        
        # Merge with original data
        merged_df = self.merge_with_original_data(reports_df)
        self.logger.info(f"Merged data contains {len(merged_df)} records")
        
        # Add quality metrics
        processed_df = self.add_quality_metrics(merged_df, reports_df)
        
        # Store processed data
        self.processed_data = processed_df
        
        # Generate summary
        summary = self.generate_summary_statistics(processed_df)
        self.logger.info(f"Data processing complete. Coverage: {summary['average_completeness']:.2%}")
        
        return processed_df, summary

    def save_submission_data(self, output_filename=None):
        """Save the processed data to submission format."""
        if self.processed_data is None:
            self.logger.error("No processed data available. Run populate_dataframe() first.")
            return False
        
        if output_filename is None:
            output_filename = "data_discovery_submission.csv"
        
        output_path = os.path.join(self.submission_path, output_filename)
        
        # Ensure submission directory exists
        os.makedirs(self.submission_path, exist_ok=True)
        
        try:
            # Save main submission file (original format)
            submission_columns = ['ID', 'NAME', 'VARIABLE', 'SRC', 'VALUE', 'CURRENCY', 'REFYEAR']
            submission_df = self.processed_data[submission_columns].copy()
            submission_df.to_csv(output_path, sep=';', index=False)
            
            # Save detailed version with quality metrics
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
        """
        Main execution method that runs the complete data processing pipeline.
        
        Args:
            save_output (bool): Whether to save the processed data to files
            output_filename (str): Custom filename for output (optional)
            verbose (bool): Whether to print detailed progress information
            
        Returns:
            tuple: (processed_dataframe, summary_statistics, success_status)
        """
        try:
            if verbose:
                print("=" * 60)
                print("DATA DISCOVERY - SUBMISSION PROCESSING")
                print("=" * 60)
                print(f"Original dataset: {len(self.dataset)} records")
                print(f"Reports path: {self.reports_path}")
                print(f"Submission path: {self.submission_path}")
                print("-" * 60)
            
            # Step 1: Populate dataframe with reports data
            if verbose:
                print("Step 1: Loading and processing data...")
            
            processed_df, summary = self.populate_dataframe()
            
            if verbose:
                print(f"✓ Processed {len(processed_df)} records")
                print(f"✓ Coverage: {summary['unique_companies']} companies")
                print(f"✓ Average completeness: {summary['average_completeness']:.1%}")
                print()
                
                # Display variable coverage
                print("Variable Coverage:")
                for var, stats in summary['variables_coverage'].iterrows():
                    print(f"  {var}: {stats['filled_count']}/{stats['total_count']} "
                          f"({stats['coverage_percentage']:.1f}%)")
                print()
                
                # Display confidence distribution
                print("Confidence Distribution:")
                for conf, count in summary['confidence_distribution'].items():
                    percentage = (count / len(processed_df)) * 100
                    print(f"  {conf}: {count} records ({percentage:.1f}%)")
                print()
                
                # Display page status
                print("Page Access Status:")
                for status, count in summary['page_status_distribution'].items():
                    percentage = (count / len(processed_df)) * 100
                    print(f"  {status}: {count} records ({percentage:.1f}%)")
                print()
            
            # Step 2: Save output files if requested
            if save_output:
                if verbose:
                    print("Step 2: Saving output files...")
                
                success = self.save_submission_data(output_filename)
                
                if success:
                    if verbose:
                        print("✓ Files saved successfully")
                        if output_filename:
                            print(f"  - Main file: {output_filename}")
                            print(f"  - Detailed file: {output_filename.replace('.csv', '_detailed.csv')}")
                        else:
                            print("  - Main file: data_discovery_submission.csv")
                            print("  - Detailed file: data_discovery_submission_detailed.csv")
                else:
                    if verbose:
                        print("✗ Error saving files")
                    return processed_df, summary, False
            
            # Step 3: Final summary
            if verbose:
                print("-" * 60)
                print("PROCESSING COMPLETE")
                print(f"✓ {summary['companies_with_sources']} companies have source URLs")
                print(f"✓ {summary['confidence_distribution'].get('HIGH', 0)} high-confidence records")
                print(f"✓ {summary['confidence_distribution'].get('MEDIUM', 0)} medium-confidence records")
                
                # Highlight any issues
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