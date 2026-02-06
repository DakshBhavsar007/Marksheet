import pdfplumber
import re
import json
import os

# Target the JS file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "new_data.js")
PDF_PATH = os.path.join(os.path.dirname(__file__), "COMPILE_MARKSHEET_SEM_3_SY_CE_IT_1_ODD_2025_T1 to T4.pdf")

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
    SY1 PDF Structure (0-indexed):
    - 0: SR NO
    - 1: Branch
    - 2: Enrollment
    - 3: Name
    - 4: Roll No
    - 5: Div
    - 6: Mentor
    - PS: 7-12 (T1, T2, T3, T4/50, T4/25, Total) -> Use Total at [12]
    - FSD: 13-18 -> Use Total at [18]
    - DE: 19-24 -> Use Total at [24]
    - FCSP: 25-30 -> Use Total at [30]
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
                    if not row or len(row) < 30:
                        continue
                    
                    # Skip header rows - check if first column is a number (SR NO)
                    sr_no = str(row[0]).strip() if row[0] else ''
                    if not sr_no.isdigit():
                        continue
                    
                    try:
                        branch = str(row[1]).strip() if row[1] else ''
                        enrollment = str(row[2]).strip() if row[2] else ''
                        name = str(row[3]).strip().upper() if row[3] else ''
                        
                        # Roll number might be a string or number
                        roll_str = str(row[4]).strip() if row[4] else '0'
                        roll = int(float(roll_str)) if roll_str.replace('.', '').isdigit() else 0
                        
                        div = str(row[5]).strip() if row[5] else ''
                        mentor = str(row[6]).strip() if row[6] else ''
                        
                        # Skip if enrollment is invalid
                        if len(enrollment) < 10:
                            continue
                        
                        # Use Total columns directly (already calculated in PDF)
                        ps_marks = parse_mark(row[12])      # PS Total
                        fsd_marks = parse_mark(row[18])     # FSD Total
                        de_marks = parse_mark(row[24])      # DE Total
                        fcsp_marks = parse_mark(row[30])    # FCSP Total
                        
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
                            'dept': 'SY1'
                        }
                        students.append(student)
                        
                    except Exception as e:
                        print(f"Error parsing row: {e}")
                        continue
    
    print(f"Extracted {len(students)} SY1 students")
    return students

def add_students_to_js(new_students):
    """Add new SY1 students to the JS data file"""
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
    
    # Remove existing SY1 students (to replace with correct data)
    existing_data = [s for s in existing_data if s.get('dept') != 'SY1']
    print(f"Removed old SY1 entries, remaining: {len(existing_data)} students")
    
    # Add new students
    added_count = 0
    for student in new_students:
        existing_data.append(student)
        added_count += 1
    
    print(f"Added {added_count} new SY1 students")
    
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
    print("--- SY1 Student Adder ---")
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
