import pandas as pd
import chardet
import sys
import os

def detect_encoding(file_path):
    """Detect the encoding of a file"""
    with open(file_path, 'rb') as file:
        raw_data = file.read(10000)  # Read first 10KB to detect encoding
        result = chardet.detect(raw_data)
        return result['encoding']

def clean_csv_encoding(input_file, output_file=None):
    """Clean CSV file and convert to UTF-8"""
    
    if output_file is None:
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_cleaned{ext}"
    
    try:
        # Detect current encoding
        print(f"Detecting encoding for {input_file}...")
        detected_encoding = detect_encoding(input_file)
        print(f"Detected encoding: {detected_encoding}")
        
        # Try to read with detected encoding first
        encodings_to_try = [detected_encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        df = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            if encoding is None:
                continue
            try:
                print(f"Trying to read with {encoding} encoding...")
                df = pd.read_csv(input_file, encoding=encoding, on_bad_lines='skip')
                used_encoding = encoding
                print(f"Successfully read file with {encoding} encoding")
                break
            except Exception as e:
                print(f"Failed with {encoding}: {str(e)}")
                continue
        
        if df is None:
            raise Exception("Could not read file with any encoding")
        
        print(f"File read successfully with {used_encoding} encoding")
        print(f"Shape: {df.shape}")
        
        # Clean problematic characters
        print("Cleaning problematic characters...")
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str)
            # Replace problematic characters
            df[col] = df[col].str.replace('\x95', '-', regex=False)  # Replace bullet point
            df[col] = df[col].str.replace('\x96', '-', regex=False)  # Replace en dash
            df[col] = df[col].str.replace('\x97', '--', regex=False) # Replace em dash
            df[col] = df[col].str.replace('\x91', "'", regex=False)  # Replace left single quote
            df[col] = df[col].str.replace('\x92', "'", regex=False)  # Replace right single quote
            df[col] = df[col].str.replace('\x93', '"', regex=False)  # Replace left double quote
            df[col] = df[col].str.replace('\x94', '"', regex=False)  # Replace right double quote
            df[col] = df[col].str.replace('\x85', '...', regex=False) # Replace ellipsis
            
        # Save as clean UTF-8
        print(f"Saving cleaned file as {output_file}...")
        df.to_csv(output_file, index=False, encoding='utf-8', quoting=1)  # quoting=1 means QUOTE_ALL
        
        print(f"✅ Successfully created cleaned file: {output_file}")
        print(f"Original file: {input_file}")
        print(f"Cleaned file: {output_file}")
        print(f"Rows: {len(df)}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        return None

def find_problematic_line(file_path):
    """Find the specific line causing issues"""
    try:
        with open(file_path, 'rb') as file:
            line_num = 0
            for line in file:
                line_num += 1
                try:
                    line.decode('utf-8')
                except UnicodeDecodeError as e:
                    print(f"Problematic line {line_num}: {e}")
                    print(f"Line content (first 100 chars): {line[:100]}")
                    if line_num > 10:  # Stop after finding first few issues
                        break
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    # You can specify the file path here or pass it as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "Unified_Candidate_Data_20250708 (All_Candidates).csv"
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        print("Please make sure the file exists in the current directory")
        sys.exit(1)
    
    print("=" * 50)
    print("CSV ENCODING CLEANER")
    print("=" * 50)
    
    # First, try to identify problematic lines
    print("\n1. Identifying problematic lines...")
    find_problematic_line(input_file)
    
    print(f"\n2. Cleaning file: {input_file}")
    cleaned_file = clean_csv_encoding(input_file)
    
    if cleaned_file:
        print(f"\n✅ Process completed successfully!")
        print(f"Use this cleaned file for your database import: {cleaned_file}")
    else:
        print(f"\n❌ Process failed. Please check the error messages above.")
