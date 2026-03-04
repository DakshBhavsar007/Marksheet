import pdfplumber
import re
import json
import argparse
import sys
import os

# Updated to target the JS file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "new_data.js")

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
                    
                    enrollment = str(row[2]).strip()
                    mark_str = str(row[7]).strip()
                    
                    if len(enrollment) < 10: 
                        continue
                        
                    mark_str_clean = mark_str.replace('\n', ' ').strip().upper()
                    
                    if mark_str_clean == 'AB' or mark_str_clean == 'NONE':
                        mark = 0.0
                        if mark_str_clean == 'AB': count_ab += 1
                    else:
                        try:
                            clean_num = mark_str.replace(' ', '')
                            mark = float(clean_num)
                        except ValueError:
                            match = re.search(r'[\d\.]+', mark_str)
                            if match:
                                mark = float(match.group(0))
                            else:
                                mark = 0.0
                    
                    marks_map[enrollment] = mark
    
    print(f"Extracted marks for {len(marks_map)} students.")
    print(f"Found {count_ab} students marked 'AB' (Absent).")
    return marks_map

def update_js_data(target_subject, marks_map):
    print(f"Updating Data file: {DATA_FILE_PATH}")
    print(f"Target Subject Key: '{target_subject}'")
    
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract array content: const data = [ ... ];
    match = re.search(r'const data = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const data' array in new_data.js.")
        return
    
    data_str = match.group(1)
    
    # 1. Add quotes to keys {roll: -> {"roll":
    # Be careful not to quote values that are already quoted
    # Basic logic: look for word characters followed by colon, excluding those in quotes (simplified)
    # Since existing lines are well formatted like: {roll: 115, div: "D4", ...}
    # We can replace (\w+): with "\1":
    
    json_str = data_str
    # Replace keys like 'roll:' with '"roll":'
    json_str = re.sub(r'(\w+):', r'"\1":', json_str)
    
    # Trailing commas are invalid in JSON, remove them
    json_str = re.sub(r',\s*\}', '}', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error during preparation: {e}")
        # Fallback debug
        # print(json_str[:500]) 
        return

    updated_count = 0
    for student in data:
        enrollment = str(student.get('enrollment', ''))
        
        # Ensure target key exists
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

    # Reconstruct JS file
    # We want format: {roll: 115, div: "D4", ...}, no quotes on keys to match style (optional but cleaner)
    # Actually, standard JSON is fine, but let's try to match the "keys without quotes" style if possible
    # or just write valid JS object literals. Valid JS allows string keys.
    # Let's write standard JSON but strip quotes from keys for aesthetic match to original file if preferred,
    # OR just write standard JS objects. 
    # Let's keep it simple: Write valid JS objects (keys can have quotes).
    
    new_data_lines = ["const data = ["]
    for i, item in enumerate(data):
        # dumps produces {"key": val}
        # We can strip quotes from keys to match original style: "key": -> key:
        line_json = json.dumps(item)
        # Remove quotes around keys
        line_js = re.sub(r'"(\w+)":', r'\1:', line_json)
        
        line = "  " + line_js
        if i < len(data) - 1: line += ","
        new_data_lines.append(line)
    new_data_lines.append("];")
    
    new_content = "\n".join(new_data_lines)
    
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("new_data.js updated successfully.")

def main():
    print("--- Marks Updater ---")
    
    if len(sys.argv) < 3:
        # Default behavior or prompt? User passes args usually
        print("Usage: python update_marks.py <pdf_file> <subject>")
        return

    pdf_input = sys.argv[1]
    subject_input = sys.argv[2].lower()

    if subject_input not in SUBJECT_MAP:
        print(f"Invalid subject '{subject_input}'. Valid options: {list(SUBJECT_MAP.keys())}")
        return

    internal_key = SUBJECT_MAP[subject_input]
    
    if not os.path.isabs(pdf_input):
        # Assume relative to this script
        pdf_input = os.path.join(os.path.dirname(DATA_FILE_PATH), pdf_input)
    
    marks = extract_marks_from_pdf(pdf_input)
    if marks:
        update_js_data(internal_key, marks)

if __name__ == "__main__":
    main()
