"""Submission script for Data Discovery."""

from submission.submission import DataExtractionSubmission


def main() -> None:
    """Run the Data Discovery submission process."""
    submission = DataExtractionSubmission()
    submission.run()


if __name__ == "__main__":
    main()
