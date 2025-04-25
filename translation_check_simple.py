import re
import random
import logging

def simple_check_translation_alignment(source_text, target_text, source_lang="en", target_lang="cs"):
    """
    Simple heuristic approach to check if two sentences are aligned
    Based on statistical properties of translations between languages
    
    Args:
        source_text (str): The source language text
        target_text (str): The target language text
        source_lang (str): ISO code for source language (en, cs, etc)
        target_lang (str): ISO code for target language
        
    Returns:
        dict: A dictionary with alignment score and analysis
    """
    # 1. Check length ratios (translations have typical length ratios)
    # English and Czech typically have around 1:1.1 to 1:1.3 ratio
    # (Czech tends to be 10-30% longer than English)
    source_length = len(source_text)
    target_length = len(target_text)
    
    length_ratio = target_length / source_length if source_length > 0 else 0
    
    # Typical en-cs length ratio range (may vary by language pair)
    if source_lang == "en" and target_lang == "cs":
        ideal_ratio_min = 0.9
        ideal_ratio_max = 1.5
    else:
        # Generic case for unknown language pairs
        ideal_ratio_min = 0.6
        ideal_ratio_max = 1.6
        
    ratio_score = 0.0
    if length_ratio >= ideal_ratio_min and length_ratio <= ideal_ratio_max:
        # Ratio is in expected range - good
        ratio_distance = min(
            abs(length_ratio - ideal_ratio_min) / (ideal_ratio_max - ideal_ratio_min),
            abs(length_ratio - ideal_ratio_max) / (ideal_ratio_max - ideal_ratio_min)
        )
        ratio_score = 1.0 - ratio_distance
    
    # 2. Check sentence structure - do both end with similar punctuation?
    source_end_punct = re.search(r'[.!?]$', source_text)
    target_end_punct = re.search(r'[.!?]$', target_text)
    
    punct_score = 1.0 if bool(source_end_punct) == bool(target_end_punct) else 0.5
    
    # 3. Similar number of sentence components (approximated by number of commas+semicolons)
    source_commas = source_text.count(',') + source_text.count(';')
    target_commas = target_text.count(',') + target_text.count(';')
    
    comma_diff = abs(source_commas - target_commas)
    comma_score = 1.0 if comma_diff == 0 else (0.8 if comma_diff == 1 else 0.6)
    
    # 4. Numbers check - translations should have the same numbers
    source_numbers = re.findall(r'\d+', source_text)
    target_numbers = re.findall(r'\d+', target_text)
    
    numbers_score = 1.0
    if source_numbers or target_numbers:
        if source_numbers != target_numbers:
            numbers_score = 0.0  # Mismatch in numbers is a strong signal of misalignment
    
    # 5. Named entities (simplified - check for capitalized words)
    source_capitals = re.findall(r'\b[A-Z][a-z]+\b', source_text)
    target_capitals = re.findall(r'\b[A-Z][a-zščřžýáíéěóúůďťňŠČŘŽÝÁÍÉĚÓÚŮĎŤŇ]+\b', target_text)
    
    # Similar number of capitalized words is a good sign
    capitals_diff = abs(len(source_capitals) - len(target_capitals))
    capitals_score = 1.0 if capitals_diff <= 1 else (0.7 if capitals_diff <= 2 else 0.4)
    
    # 6. Check for extreme differences in the number of words
    source_words = len(re.findall(r'\b\w+\b', source_text))
    target_words = len(re.findall(r'\b\w+\b', target_text))
    
    word_ratio = target_words / source_words if source_words > 0 else 0
    word_ratio_score = 1.0
    
    # Extreme difference in word count is suspicious
    if word_ratio < 0.5 or word_ratio > 2.0:
        word_ratio_score = 0.2
    
    # Calculate weighted total score
    weights = {
        'ratio_score': 0.15,
        'punct_score': 0.10, 
        'comma_score': 0.10,
        'numbers_score': 0.30,  # Strong signal
        'capitals_score': 0.25,
        'word_ratio_score': 0.10
    }
    
    total_score = (
        weights['ratio_score'] * ratio_score +
        weights['punct_score'] * punct_score +
        weights['comma_score'] * comma_score +
        weights['numbers_score'] * numbers_score +
        weights['capitals_score'] * capitals_score +
        weights['word_ratio_score'] * word_ratio_score
    )
    
    # Generate explanation
    explanation = []
    if ratio_score < 0.7:
        explanation.append(f"Unusual length ratio ({length_ratio:.2f})")
    if punct_score < 1.0:
        explanation.append("Ending punctuation mismatch")
    if comma_score < 0.8:
        explanation.append("Different sentence structure (commas)")
    if numbers_score < 1.0:
        explanation.append("Numbers don't match")
    if capitals_score < 0.7:
        explanation.append("Capitalized words don't match")
    if word_ratio_score < 0.5:
        explanation.append(f"Suspicious word count ratio ({word_ratio:.2f})")
    
    if not explanation:
        explanation = ["Sentences appear well-aligned"]
    
    confidence = 0.6  # Simple heuristics have limited confidence
    
    return {
        "alignment_score": total_score,
        "confidence": confidence,
        "explanation": "; ".join(explanation),
        "is_aligned": total_score >= 0.7  # Consider 0.7+ as reasonably aligned
    }

def batch_check_translations(source_sentences, target_sentences, sample_size=5):
    """
    Check a random sample of sentence pairs to evaluate overall alignment quality.
    
    Args:
        source_sentences (list): List of source language sentences
        target_sentences (list): List of target language sentences
        sample_size (int): Number of random pairs to check
        
    Returns:
        dict: Overall alignment statistics
    """
    # Ensure we don't try to sample more than we have
    actual_sample_size = min(sample_size, len(source_sentences), len(target_sentences))
    
    # If we have fewer than 10 sentences, check all of them
    if len(source_sentences) <= 10:
        indices = list(range(len(source_sentences)))
    else:
        # Sample random indices without replacement
        indices = random.sample(range(len(source_sentences)), actual_sample_size)
    
    results = []
    total_score = 0
    aligned_count = 0
    
    for idx in indices:
        source = source_sentences[idx]
        target = target_sentences[idx]
        
        # Skip very short sentences which might be headers or similar
        if len(source.split()) < 3 or len(target.split()) < 3:
            continue
            
        result = simple_check_translation_alignment(source, target)
        result["source"] = source
        result["target"] = target
        result["index"] = idx
        
        results.append(result)
        total_score += result["alignment_score"]
        
        if result["is_aligned"]:
            aligned_count += 1
    
    # Calculate overall stats
    checked_count = len(results)
    avg_score = total_score / checked_count if checked_count > 0 else 0
    aligned_pct = (aligned_count / checked_count * 100) if checked_count > 0 else 0
    
    return {
        "overall_alignment_score": avg_score,
        "aligned_percentage": aligned_pct,
        "checked_count": checked_count,
        "aligned_count": aligned_count,
        "details": results
    }

# Simple test function
def test_alignment_check():
    # Good alignment example
    good_pairs = [
        (
            "The quick brown fox jumps over the lazy dog.",
            "Rychlá hnědá liška skáče přes líného psa."
        ),
        (
            "She visited Prague, Vienna, and Budapest during her European tour.",
            "Během své evropské cesty navštívila Prahu, Vídeň a Budapešť."
        ),
        (
            "The meeting on April 15, 2023 was very productive and we discussed the new version 2.0.4 of our software.",
            "Schůzka dne 15. dubna 2023 byla velmi produktivní a diskutovali jsme o nové verzi 2.0.4 našeho softwaru."
        )
    ]
    
    # Bad alignment example
    bad_pairs = [
        (
            "The quick brown fox jumps over the lazy dog.",
            "Dnes je krásný den a svítí slunce."  # "Today is a beautiful day and the sun is shining."
        ),
        (
            "She visited Prague, Vienna, and Budapest during her European tour.",
            "Teplota v Praze je dnes 25 stupňů."  # "The temperature in Prague today is 25 degrees."
        ),
        (
            "The GDP of Germany increased by 2.3% in 2019.",
            "Populace Německa je přibližně 83 milionů obyvatel."  # "The population of Germany is approximately 83 million people."
        )
    ]
    
    print("Testing good alignments:")
    for i, (source, target) in enumerate(good_pairs):
        print(f"\nPair {i+1}:")
        print(f"EN: {source}")
        print(f"CS: {target}")
        result = simple_check_translation_alignment(source, target)
        print(f"Score: {result['alignment_score']:.2f}, Aligned: {result['is_aligned']}")
        print(f"Explanation: {result['explanation']}")
    
    print("\nTesting bad alignments:")
    for i, (source, target) in enumerate(bad_pairs):
        print(f"\nPair {i+1}:")
        print(f"EN: {source}")
        print(f"CS: {target}")
        result = simple_check_translation_alignment(source, target)
        print(f"Score: {result['alignment_score']:.2f}, Aligned: {result['is_aligned']}")
        print(f"Explanation: {result['explanation']}")
    
    # Test batch functionality
    print("\nTesting batch check:")
    all_source = [pair[0] for pair in good_pairs + bad_pairs]
    all_target = [pair[1] for pair in good_pairs + bad_pairs]
    
    batch_result = batch_check_translations(all_source, all_target, sample_size=6)
    print(f"Overall alignment score: {batch_result['overall_alignment_score']:.2f}")
    print(f"Aligned percentage: {batch_result['aligned_percentage']:.1f}%")
    print(f"Checked count: {batch_result['checked_count']}")
    print(f"Aligned count: {batch_result['aligned_count']}")

if __name__ == "__main__":
    test_alignment_check()