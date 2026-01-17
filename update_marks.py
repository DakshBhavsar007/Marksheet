import pdfplumber
import re
import json
import argparse
import sys
import os

HTML_PATH = os.path.join(os.path.dirname(__file__), "28.html")

# Mapping user terms to internal keys
# User might type: "python", "fsd", "de"
# Internal keys: "ps", "fsd", "fcsp", "de"
SUBJECT_MAP = {
    "ps": "ps",
    "fsd": "fsd",
    "de": "de",
    "python": "fcsp", 
    "fcsp": "fcsp"
}

def extract_marks_from_pdf(pdf_path):
    marks_map = {}
    print(f"Reading PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        count_ab = 0
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 8: continue
                    
                    # Assuming format: [Sr, Branch, Enrollment, Name, Roll, Div, Mentor, Mark]
                    # Index 2: Enrollment
                    # Index 7: Mark
                    enrollment = str(row[2]).strip()
                    mark_str = str(row[7]).strip()
                    
                    if len(enrollment) < 10: # content based validation
                        continue
                        
                    mark_str_clean = mark_str.replace('\n', ' ').strip().upper()
                    
                    if mark_str_clean == 'AB' or mark_str_clean == 'NONE':
                        mark = 0.0
                        if mark_str_clean == 'AB': count_ab += 1
                    else:
                        try:
                            # Handle potential spacing issues "34 5" -> 34.5 logic if needed
                            # For now standard float conversion, strip spaces
                            clean_num = mark_str.replace(' ', '')
                            mark = float(clean_num)
                        except ValueError:
                            # Try finding first float
                            match = re.search(r'[\d\.]+', mark_str)
                            if match:
                                mark = float(match.group(0))
                            else:
                                mark = 0.0
                    
                    marks_map[enrollment] = mark
    
    print(f"Extracted marks for {len(marks_map)} students.")
    print(f"Found {count_ab} students marked 'AB' (Absent).")
    return marks_map

def update_html(target_subject, marks_map):
    print(f"Updating HTML file: {HTML_PATH}")
    print(f"Target Subject Key: '{target_subject}'")
    
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'const data = (\[.*?\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const data' in HTML.")
        return
    
    data_str = match.group(1)
    # Lazy JSON parser (valid JS object to valid JSON)
    json_str = re.sub(r'(\w+):', r'"\1":', data_str)
    json_str = re.sub(r',\s*}', '}', json_str)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        return

    updated_count = 0
    for student in data:
        enrollment = str(student.get('enrollment', ''))
        
        # Ensure the subject key exists in the student object
        if target_subject not in student:
            student[target_subject] = 0.0

        if enrollment in marks_map:
            pdf_mark = marks_map[enrollment]
            
            # Logic: New = Old + (PDF / 2)
            old_val = float(student.get(target_subject, 0))
            increment = pdf_mark / 2.0
            new_val = old_val + increment
            
            student[target_subject] = new_val
            updated_count += 1
    
    print(f"Updated records for {updated_count} students.")

    # Write back
    new_data_lines = ["const data = ["]
    for i, item in enumerate(data):
        line = "  " + json.dumps(item)
        if i < len(data) - 1: line += ","
        new_data_lines.append(line)
    new_data_lines.append("];")
    
    new_data_str = "\n".join(new_data_lines)
    new_content = content.replace(match.group(0), new_data_str)
    
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("HTML updated successfully.")

def main():
    print("--- Marks Updater ---")
    print("Rules: Extracts marks (out of 50) from PDF, divides by 2, adds to existing score.")
    
    # Simple interactive mode if no args
    if len(sys.argv) < 3:
        pdf_input = input("Enter PDF filename (e.g. marks.pdf): ").strip()
        subject_input = input("Enter subject (fsd, python, de, ps): ").strip().lower()
    else:
        pdf_input = sys.argv[1]
        subject_input = sys.argv[2].lower()

    if subject_input not in SUBJECT_MAP:
        print(f"Invalid subject '{subject_input}'. Valid options: {list(SUBJECT_MAP.keys())}")
        return

    internal_key = SUBJECT_MAP[subject_input]
    
    # Handle full path or relative
    if not os.path.isabs(pdf_input):
        pdf_input = os.path.join(os.path.dirname(HTML_PATH), pdf_input)
    
    marks = extract_marks_from_pdf(pdf_input)
    if marks:
        update_html(internal_key, marks)

if __name__ == "__main__":
    main()
