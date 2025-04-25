import pandas as pd
import logging
import re
import string
from translation_check_simple import simple_check_translation_alignment, batch_check_translations

def process_excel_file(input_path, output_path, source_column='en-US', target_column='cs-CZ', check_alignment=True):
    """
    Process an Excel file containing bilingual text data and split it into sentence pairs.
    
    Args:
        input_path (str): Path to the input Excel file
        output_path (str): Path where the output Excel file will be saved
        source_column (str): Name of the source language column
        target_column (str): Name of the target language column
        
    Returns:
        dict: Statistics about the processing
    """
    logging.debug(f"Processing file: {input_path}")
    logging.debug(f"Using columns: {source_column} and {target_column}")
    
    # Read the excel file
    try:
        df = pd.read_excel(input_path)
    except Exception as e:
        logging.error(f"Error reading Excel file: {str(e)}")
        raise Exception(f"Could not read Excel file: {str(e)}")
    
    # Verify that the required columns exist
    if source_column not in df.columns or target_column not in df.columns:
        available_cols = ', '.join(df.columns)
        logging.error(f"Required columns not found. Available columns: {available_cols}")
        raise Exception(f"Required columns ({source_column}, {target_column}) not found. Available columns: {available_cols}")
    
    # Initialize lists to hold split data
    source_sentences = []
    target_sentences = []
    row_references = []  # Keep track of original row for better traceability
    
    # Statistics tracking
    stats = {
        'total_rows': len(df),
        'processed_rows': 0,
        'skipped_rows': 0,
        'total_sentences': 0,
        'mismatched_sentences': 0
    }
    
    # Regular expression for splitting sentences
    # Enhanced to handle more edge cases:
    # - Common abbreviations in English (Mr., Dr., etc.)
    # - Common abbreviations in Czech (p., č., atd.)
    # - Numeric expressions (1.5, 2.3.4)
    # - Different punctuation marks
    
    # Simplified approach for better compatibility
    # This pattern looks for sentence endings (., !, ?) followed by spaces or newlines
    # while avoiding common abbreviations
    sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
    
    logging.debug(f"Using sentence pattern: {sentence_pattern}")
    
    # No longer splitting long sentences as per user request
    
    # Iterate over each row and split the sentences
    for index, row in df.iterrows():
        try:
            # Get the text from both columns, ensuring they're strings
            source_text = str(row[source_column])
            target_text = str(row[target_column])
            
            # Skip empty rows
            if pd.isna(source_text) or pd.isna(target_text) or source_text.strip() == '' or target_text.strip() == '':
                stats['skipped_rows'] += 1
                logging.debug(f"Skipping empty row at index {index}")
                continue
            
            # Debug the text we're trying to split
            logging.debug(f"Source text length: {len(source_text)}")
            logging.debug(f"Target text length: {len(target_text)}")
            if len(source_text) < 100:  # Only log short texts to avoid log spam
                logging.debug(f"Source text: {source_text}")
                logging.debug(f"Target text: {target_text}")
            
            # Try two methods - first the regex approach
            source_text_sentences = re.split(sentence_pattern, source_text)
            target_text_sentences = re.split(sentence_pattern, target_text)
            
            # Debug
            logging.debug(f"Sentences after regex split - source: {len(source_text_sentences)}, target: {len(target_text_sentences)}")
            
            # If regex didn't work well, try alternative splitting
            if len(source_text_sentences) <= 1 and len(source_text) > 50:
                logging.debug("Regex pattern didn't split sentences well, trying alternative splitting")
                
                # More elaborate sentence splitting - handles common abbreviations
                # This regex looks for sentence boundaries while ignoring common abbreviations
                alt_pattern = r'(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bMs)(?<!\bProf)(?<!\bRev)(?<!\bSt)(?<!\bp)(?<!\bč)(?<!\bstr)(?<!\br)\.\s+[A-Z0-9]'
                
                # Find all matches and split based on positions
                source_matches = list(re.finditer(alt_pattern, source_text))
                target_matches = list(re.finditer(alt_pattern, target_text))
                
                # If we found sentence boundaries
                if source_matches and target_matches:
                    source_text_sentences = []
                    prev_end = 0
                    for match in source_matches:
                        end_pos = match.start() + 1  # Include the period
                        source_text_sentences.append(source_text[prev_end:end_pos].strip())
                        prev_end = match.start() + 1
                    # Add the last part
                    if prev_end < len(source_text):
                        source_text_sentences.append(source_text[prev_end:].strip())
                        
                    target_text_sentences = []
                    prev_end = 0
                    for match in target_matches:
                        end_pos = match.start() + 1  # Include the period
                        target_text_sentences.append(target_text[prev_end:end_pos].strip())
                        prev_end = match.start() + 1
                    # Add the last part
                    if prev_end < len(target_text):
                        target_text_sentences.append(target_text[prev_end:].strip())
                else:
                    # Fallback to simple splitting with period
                    simple_splits = source_text.split('. ')
                    source_text_sentences = [(s + ".").strip() for s in simple_splits if s.strip()]
                    
                    simple_splits = target_text.split('. ')
                    target_text_sentences = [(s + ".").strip() for s in simple_splits if s.strip()]
                
                logging.debug(f"Sentences after alternative split - source: {len(source_text_sentences)}, target: {len(target_text_sentences)}")
            
            # Clean up the sentences (remove extra whitespace)
            source_text_sentences = [s.strip() for s in source_text_sentences if s.strip()]
            target_text_sentences = [s.strip() for s in target_text_sentences if s.strip()]
            
            logging.debug(f"Cleaned sentences - source: {len(source_text_sentences)}, target: {len(target_text_sentences)}")
            
            # No longer splitting long sentences
            refined_source_sentences = source_text_sentences
            refined_target_sentences = target_text_sentences
            
            # Check if sentence counts match
            if len(refined_source_sentences) != len(refined_target_sentences):
                logging.warning(f"Mismatch in sentence count at row {index}. Source: {len(refined_source_sentences)}, Target: {len(refined_target_sentences)}")
                stats['mismatched_sentences'] += 1
                
                # Attempt to align sentences if possible 
                # For simplicity, if counts don't match but are close, we take the smaller count
                if abs(len(refined_source_sentences) - len(refined_target_sentences)) <= 2:
                    min_count = min(len(refined_source_sentences), len(refined_target_sentences))
                    refined_source_sentences = refined_source_sentences[:min_count]
                    refined_target_sentences = refined_target_sentences[:min_count]
                else:
                    stats['skipped_rows'] += 1
                    continue
            
            # Add sentences to the lists
            for source_sent, target_sent in zip(refined_source_sentences, refined_target_sentences):
                # Fix punctuation - don't add periods if already present
                # Also remove any double periods that might have been created
                if source_sent:
                    if source_sent.endswith('..'):
                        source_sent = source_sent[:-1]
                    elif not any(source_sent.endswith(p) for p in ['.', '!', '?']):
                        source_sent = source_sent + '.'
                        
                if target_sent:
                    if target_sent.endswith('..'):
                        target_sent = target_sent[:-1]
                    elif not any(target_sent.endswith(p) for p in ['.', '!', '?']):
                        target_sent = target_sent + '.'
                    
                source_sentences.append(source_sent)
                target_sentences.append(target_sent)
                row_references.append(index + 1)  # Excel rows are 1-indexed for users
                stats['total_sentences'] += 1
            
            stats['processed_rows'] += 1
            
        except Exception as e:
            logging.error(f"Error processing row {index}: {str(e)}")
            stats['skipped_rows'] += 1
    
    # Check alignment of the sentence pairs
    alignment_results = None
    poorly_aligned_pairs = []
    
    if check_alignment and source_sentences and target_sentences:
        # Get source language code from column name (assuming format like "en-US")
        source_lang = source_column.split('-')[0].lower() if '-' in source_column else 'en'
        target_lang = target_column.split('-')[0].lower() if '-' in target_column else 'cs'
        
        try:
            # Run batch alignment check on the sentences
            logging.info(f"Checking translation alignment for {len(source_sentences)} sentence pairs")
            # Use a sample of sentences for efficiency (max 50)
            sample_size = min(50, len(source_sentences))
            
            alignment_results = batch_check_translations(
                source_sentences, 
                target_sentences, 
                sample_size=sample_size
            )
            
            # Add alignment statistics
            stats['alignment_score'] = alignment_results['overall_alignment_score']
            stats['aligned_percentage'] = alignment_results['aligned_percentage']
            stats['alignment_checked_count'] = alignment_results['checked_count']
            
            # Identify poorly aligned pairs
            if 'details' in alignment_results:
                for detail in alignment_results['details']:
                    if not detail['is_aligned']:
                        poorly_aligned_pairs.append({
                            'index': detail['index'],
                            'source': detail['source'],
                            'target': detail['target'],
                            'score': detail['alignment_score'],
                            'explanation': detail['explanation']
                        })
                        
            stats['poorly_aligned_count'] = len(poorly_aligned_pairs)
            
        except Exception as e:
            logging.error(f"Error during alignment check: {str(e)}")
            # Don't fail the whole process if alignment check fails
            stats['alignment_error_msg'] = str(e)
    
    # Create a new DataFrame with the split sentences
    result_data = {
        source_column: source_sentences, 
        target_column: target_sentences,
        'original_row': row_references  # Add reference to original row for traceability
    }
    
    # Add alignment score column if available
    if alignment_results:
        # For each sentence pair, calculate individual alignment score
        alignment_scores = []
        alignment_issues = []
        
        for i in range(len(source_sentences)):
            # Default values
            score = -1  # -1 means not checked
            issues = ""
            
            # Check if we have checked this pair
            for detail in alignment_results.get('details', []):
                if detail['index'] == i:
                    score = detail['alignment_score']
                    issues = detail['explanation'] if not detail['is_aligned'] else ''
                    break
                    
            alignment_scores.append(score)
            alignment_issues.append(issues)
        
        result_data['alignment_score'] = alignment_scores
        result_data['alignment_issues'] = alignment_issues
    
    # Create the result DataFrame 
    new_df = pd.DataFrame(result_data)
    
    # Save to a new excel file
    try:
        new_df.to_excel(output_path, index=False)
        logging.info(f"Saved processed file to {output_path} with {stats['total_sentences']} sentence pairs")
    except Exception as e:
        logging.error(f"Error saving Excel file: {str(e)}")
        raise Exception(f"Could not save output file: {str(e)}")
    
    return stats
