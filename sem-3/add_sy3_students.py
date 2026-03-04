import pdfplumber
import re
import json
import os

# Target the JS file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "new_data.js")
PDF_PATH = os.path.join(os.path.dirname(__file__), "COMPILED_THEORY_MARKSHEET_SEM_III_SY CEIT 3_ODD_2025-26_T1 TO T4.pdf")

def parse_mark(mark_str):
    """Parse a mark value, handling AB, None, empty strings"""
    if mark_str is None:
        return 0.0
    mark_str = str(mark_str).strip().upper()
    if mark_str == '' or mark_str == 'AB' or mark_str == 'NONE':
        return 0.0
    try:
        # Remove any whitespace and parse
        clean_num = mark_str.replace(' ', '').replace('\n', '')
        return float(clean_num)
    except ValueError:
        match = re.search(r'[\d\.]+', mark_str)
        if match:
            return float(match.group(0))
        return 0.0

def extract_students_from_pdf(pdf_path):
    """
    Extracts student data from compiled theory marksheet PDF.
    Structure (0-indexed):
    - 0: SR NO
    - 1: Roll No
    - 2: Div
    - 3: Mentor
    - 4: Branch
    - 5: Enrollment
    - 6: Name
    - 7-10: PS (T1, T2, T3, T4)
    - 11-14: FSD (T1, T2, T3, T4)
    - 15-18: FCSP (T1, T2, T3, T4)
    - 19-22: DE (T1, T2, T3, T4)
    """
    students = []
    print(f"Reading PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            
            for table in tables:
                for row in table:
                    if not row or len(row) < 20:
                        continue
                    
                    # Skip header rows
                    sr_no = str(row[0]).strip() if row[0] else ''
                    if not sr_no.isdigit():
                        continue
                    
                    try:
                        roll = int(str(row[1]).strip()) if row[1] else 0
                        div = str(row[2]).strip() if row[2] else ''
                        mentor = str(row[3]).strip() if row[3] else ''
                        branch = str(row[4]).strip() if row[4] else ''
                        enrollment = str(row[5]).strip() if row[5] else ''
                        name = str(row[6]).strip().upper() if row[6] else ''
                        
                        # Skip if enrollment is invalid
                        if len(enrollment) < 10:
                            continue
                        
                        # Sum marks for each subject (T1 + T2 + T3 + T4/2)
                        # T1, T2, T3 are out of 25 each, T4 is out of 50 (we take half)
                        ps_marks = parse_mark(row[7]) + parse_mark(row[8]) + parse_mark(row[9]) + parse_mark(row[10]) / 2
                        fsd_marks = parse_mark(row[11]) + parse_mark(row[12]) + parse_mark(row[13]) + parse_mark(row[14]) / 2
                        fcsp_marks = parse_mark(row[15]) + parse_mark(row[16]) + parse_mark(row[17]) + parse_mark(row[18]) / 2
                        de_marks = parse_mark(row[19]) + parse_mark(row[20]) + parse_mark(row[21]) + parse_mark(row[22]) / 2
                        
                        student = {
                            'roll': roll,
                            'div': div,
                            'branch': branch,
                            'enrollment': enrollment,
                            'name': name,
                            'mentor': mentor,
                            'ps': round(ps_marks, 2),
                            'fsd': round(fsd_marks, 2),
                            'fcsp': round(fcsp_marks, 2),
                            'de': round(de_marks, 2),
                            'dept': 'SY3'
                        }
                        students.append(student)
                        
                    except Exception as e:
                        print(f"Error parsing row: {e}")
                        continue
    
    print(f"Extracted {len(students)} SY3 students")
    return students

def add_students_to_js(new_students):
    """Add new SY3 students to the JS data file"""
    print(f"Updating Data file: {DATA_FILE_PATH}")
    
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract array content: const data = [ ... ];
    match = re.search(r'const data = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const data' array in new_data.js.")
        return
    
    data_str = match.group(1)
    
    # Convert to JSON format
    json_str = data_str
    json_str = re.sub(r'(\w+):', r'"\1":', json_str)
    json_str = re.sub(r',\s*\}', '}', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    
    try:
        existing_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        return
    
    # Get existing SY3 enrollments to avoid duplicates
    existing_sy3_enrollments = set(
        s.get('enrollment', '') for s in existing_data if s.get('dept') == 'SY3'
    )
    
    # Add new students (only if not already present)
    added_count = 0
    for student in new_students:
        if student['enrollment'] not in existing_sy3_enrollments:
            existing_data.append(student)
            added_count += 1
    
    print(f"Added {added_count} new SY3 students (skipped {len(new_students) - added_count} duplicates)")
    
    # Reconstruct JS file
    new_data_lines = ["const data = ["]
    for i, item in enumerate(existing_data):
        line_json = json.dumps(item)
        line_js = re.sub(r'"(\w+)":', r'\1:', line_json)
        line = "  " + line_js
        if i < len(existing_data) - 1:
            line += ","
        new_data_lines.append(line)
    new_data_lines.append("];")
    
    new_content = "\n".join(new_data_lines)
    
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("new_data.js updated successfully.")

def main():
    print("--- SY3 Student Adder ---")
    print(f"PDF Path: {PDF_PATH}")
    
    students = extract_students_from_pdf(PDF_PATH)
    
    if students:
        # Show first 3 students as sample
        print("\nSample extracted students:")
        for s in students[:3]:
            print(f"  {s['name']}: PS={s['ps']}, FSD={s['fsd']}, FCSP={s['fcsp']}, DE={s['de']}")
        
        add_students_to_js(students)
        
if __name__ == "__main__":
    main()
