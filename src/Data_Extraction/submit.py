"""Submission script for Data Discovery."""

from Data_Extraction.submission.submission import DataDiscoverySubmission


def main() -> None:
    """Run the Data Discovery submission process."""
    submission = DataDiscoverySubmission()
    submission.run()


if __name__ == "__main__":
    main()
