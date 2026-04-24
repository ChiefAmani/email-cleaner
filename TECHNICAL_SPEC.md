# TECHNICAL_SPEC.md

## Project Overview
This project provides a web-based tool to clean and standardize customer data from a CSV file. It will process a CSV containing customer information, remove duplicates, filter invalid entries, standardize phone numbers, split names, and assess email bounce risk, providing a cleaned dataset and a list of removed emails.

## Tech Stack
- Python==3.9.18
- Flask==3.0.2
- pandas==2.2.1
- phonenumbers==8.13.32
- HTML5
- CSS3
- JavaScript

## File Tree
```
.
|-- app.py
|-- templates/
|   |-- index.html
|-- static/
|   |-- style.css
|-- requirements.txt
```

## API Endpoints

### Endpoint 1: File Upload and Processing
- Method: POST
- Path: /upload
- Request body: multipart/form-data containing 'file' (CSV file)
- Response: JSON object containing:
  - `cleaned_data_url`: URL to download the cleaned CSV.
  - `deleted_emails_url`: URL to download the list of deleted emails.
  - `message`: Status message.
- Auth: None

## Environment Variables
- None required for basic functionality.

## Dependencies
```
Flask==3.0.2
pandas==2.2.1
phonenumbers==8.13.32
```

## Python Script Logic (app.py)

### 1. CSV Parsing
- Reads uploaded CSV file into a pandas DataFrame.
- Expected columns: 'Name', 'Email', 'Phone Number'.

### 2. Data Cleaning and Transformation
#### a. Remove Duplicates
- Identifies and removes rows where 'Name', 'Email', and 'Phone Number' are identical.
- Prioritizes the first occurrence.

#### b. Filter Invalid Entries
- Removes rows where 'Email' is empty or null.
- Removes rows where 'Phone Number' is empty or null.

#### c. Phone Number Standardization
- Uses the `phonenumbers` library to parse and format phone numbers into E.164 format (e.g., '+15551234567').
- Invalid or unparseable phone numbers will be marked as null or an empty string.

#### d. Name Splitting
- Splits the 'Name' column into 'First Name' and 'Last Name' columns.
- Handles cases with middle names or complex name structures by taking the first word as 'First Name' and the rest as 'Last Name'.

#### e. Email Bounce Chance Algorithm
- **Validation:** Performs basic regex validation to check for common email format errors (e.g., missing '@', invalid domain characters).
- **Bounce Chance Heuristic:**
    - Emails failing basic regex validation are considered high bounce risk.
    - Placeholder for future integration with an external email validation API (e.g., ZeroBounce, NeverBounce) for more accurate bounce chance assessment. For this initial version, a simple domain check (e.g., checking for common disposable email domains or non-existent TLDs) can be implemented as a heuristic.
- **Deletion:** Rows associated with high bounce chance emails are moved to a separate DataFrame.
- **Deleted Emails List:** Generates a CSV file containing only the 'Email' addresses that were deleted due to high bounce chance.

### 3. Output Generation
- **Cleaned CSV:** Generates a new CSV file with the cleaned, sorted, and transformed data, including 'First Name' and 'Last Name' columns.
- **Deleted Emails CSV:** Generates a CSV file listing all emails identified as high bounce risk and subsequently deleted.

## HTML Interface Requirements (templates/index.html)

### 1. File Upload
- A form with an input field of type `file` that accepts CSV files.
- A submit button to trigger the upload and processing.

### 2. Process Trigger
- The submit button will send the CSV file to the `/upload` endpoint.

### 3. Result Display
- Upon successful processing, the page will display:
    - A link to download the cleaned CSV file.
    - A link to download the list of deleted emails.
    - A message indicating the success or failure of the operation.

## CSS Styling (static/style.css)
- Basic styling for a clean and user-friendly interface.
- Responsive design considerations.
