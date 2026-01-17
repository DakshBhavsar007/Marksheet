# How to Extract Marks from PDF

This guide explains how to use the `update_marks.py` script to extract marks from a PDF file and update the `28.html` marksheet.

## Prerequisites

1.  **Python**: Ensure Python is installed.
2.  **Libraries**: You need `pdfplumber`. Install it if you haven't:
    ```bash
    pip install pdfplumber
    ```

## Files

-   `28.html`: The main marksheet file (database).
-   `update_marks.py`: The Python script that performs the extraction and update.
-   `Your_PDF_File.pdf`: The source PDF containing student results.

## How to Run

1.  Open a terminal (Command Prompt or PowerShell) and navigate to this folder:
    ```bash
    cd c:\Users\parul\Desktop\html\marksheet
    ```

2.  Run the script with the PDF filename and the subject code:
    ```bash
    python update_marks.py <PDF_FILENAME> <SUBJECT_CODE>
    ```

### Subject Codes

-   `ps`: Probability & Statistics
-   `fsd`: Full Stack Development
-   `fcsp` or `python`: FCSP / Python
-   `de`: Digital Electronics

### Example Command

To extract marks for **FSD** from a file named `Marksheet_SY4.pdf`:

```bash
python update_marks.py Marksheet_SY4.pdf fsd
```

## How It Works

1.  The script reads the PDF and looks for a table with Enrollment Numbers and Marks.
2.  It extracts the mark (validating 'AB' as 0).
3.  It divides the extracted mark by **2**.
4.  It adds this value to the *existing* mark in `28.html` for that specific subject.
5.  It saves the updated data back to `28.html`.

> **Note:** The script assumes the PDF table format has the Enrollment Number in the 3rd column (index 2) and Marks in the 8th column (index 7).
