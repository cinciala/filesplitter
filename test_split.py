import pandas as pd
import tempfile
import os
from text_splitter import process_excel_file

def create_test_file():
    """Creates a simple test Excel file with some bilingual text."""
    # Sample data with English and Czech text - mix of good and bad alignments
    data = {
        'en-US': [
            'This is a test sentence. This is another sentence.',
            'Hello world! How are you doing today?',
            'Mr. Smith went to Washington D.C. He had a meeting.',
            'The company increased profits by 15% in Q2 2023.',
            'Please review the document by Friday, May 10th.',
            'They bought a new car for $25,000 last month.'
        ],
        'cs-CZ': [
            'Toto je testovací věta. Toto je další věta.',
            'Ahoj světe! Jak se dnes máš?',
            'Pan Smith jel do Washingtonu D.C. Měl schůzku.',
            'Společnost měla v minulém čtvrtletí ztrátu 5%.', # Misaligned: "The company had a 5% loss last quarter"
            'Prosím, zkontrolujte dokument do pátku, 10. května.',
            'Koupili si nový dům za 5.000.000 Kč.' # Misaligned: "They bought a new house for 5,000,000 CZK"
        ]
    }
    
    # Create a DataFrame and save to Excel
    df = pd.DataFrame(data)
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, 'test_input.xlsx')
    df.to_excel(input_path, index=False)
    
    print(f"Created test file at: {input_path}")
    return input_path

def run_test():
    """Tests the sentence splitting functionality."""
    input_path = create_test_file()
    output_path = input_path.replace('input', 'output')
    
    print("\nProcessing test file with alignment check enabled...")
    result = process_excel_file(input_path, output_path, check_alignment=True)
    
    print("\nProcessing results:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\nOutput content:")
    try:
        output_df = pd.read_excel(output_path)
        print(output_df)
    except Exception as e:
        print(f"Error reading output file: {str(e)}")

if __name__ == "__main__":
    run_test()