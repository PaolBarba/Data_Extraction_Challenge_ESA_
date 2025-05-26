# Starting Kit

This starting kit is here to help you with preparing the submission.zip file.

It contains the following files:

- This `README.md` file

- A `extraction.csv` file containing a sample of the extraction.csv file
  that you will have to submit

- A `extraction_approach_description.docx` file, used to describe the
  approach you used to generate the `extraction.csv` file

## Structure of the `submission.zip` file

The submission.zip file should only contain the following files:

```
submission.zip
├── extraction.csv
├── extraction_approach_description.docx
└── code.zip
```

Where the `code.zip` file contains the code used to generate the `extraction.csv`
file.

> NOTE: DO NOT CHANGE THE NAMES OF THE FILES OR THE STRUCTURE OF THE `submission.zip`
> FILE.

To compete for the Accuracy, Reusability and Innovativeness Awards, you need to submit the
`extraction.csv` file, the `extraction_approach_description.docx` file, and the `code.zip`
file. All three files are required to compete for either of the awards.


## Structure of the `extraction.csv` file

The `extraction.csv` file should contain the following columns:

- `ID`: the technical ID of the Multinational Enterprise (MNE) group
- `NAME`: the name of the Multinational Enterprise (MNE) group
- `VARIABLE`: the variable to be extracted
- `SRC`: the source of the information in URL format
- `VALUE`: the extracted financial data
- `CURRENCY`: the currency when applicable
- `REFYEAR`: the reference year of the extracted information

> NOTE: The `extraction.csv` file SHOULD contain the header.

Teams are required to extract annual financial data for 200 MNE Group cases with unique technical IDs and NAMEs. The ID and NAME for a unique case appears in 6 consecutive rows. The teams are required to extract the financial data [VALUE] as identified in column 3 [VARIABLE], provide the source of that information [SRC], the currency when applicable [CURRENCY] and the reference year T of the extracted information [REFYEAR]. When applicable, the [VALUE] must be provided as a full integer number.

The value of the variable must correspond to the following information:

- Country of the MNE Group (specifically, the country where the headquarter of the MNE Group is established). The value of the country should be listed in ISO 3166-1 alpha-2 (2-character code).

- Number of employees of the MNE Group worldwide for the reference year T.
- Net turnover of the MNE Group for the reference year T expressed in nominal value. This value should be an integer.
- Total assets of the MNE group for reference year T expressed in nominal value. This value should be an integer.
- Website of the MNE Group (e.g. the Website of the MNE group).
- The main activity of the MNE Group according to NACE codes [7]; Activity: 3-character code of original NACE v2 activity code. It should follow the code list original (un-updated) NACE v2. In other words, it should NOT be filled in with NACE v2.1. The 3-character string will be evaluated from left to right, meaning that strings shorter than 3 characters are admissible (thus, submitting e.g. only section would be admissible; "A" would be an example of such a submission).

Along with the value of the variable, the team must also provide the following:

- The full path source [SRC] from which the variable was extracted (e.g. the [SRC] could be the URL of the Wikipedia page).
- The currency [CURRENCY] must be provided for monetary values only and according to ISO 4217 (https://www.iso.org/iso-4217-currency-codes.html).
- Reference year T of extracted information [REFYEAR];
  - The REFYEAR indicated should be the year of the final month of the financial data
  - Examples:
    - If the annual financial report is from Jan. 2022 – Dec. 2022, the REFYEAR is indicated as 2022.
    - If the annual financial report is from Nov. 2022 – Nov. 2023, the REFYEAR is indicated as 2023.
    - If the annual financial report is from Feb. 2023 – Feb. 2024, the REFYEAR is indicated as 2024.