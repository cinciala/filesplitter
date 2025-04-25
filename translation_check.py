import os
import logging
import json
from openai import OpenAI

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
MODEL = "gpt-4o"

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def check_translation_alignment(source_text, target_text, source_lang="English", target_lang="Czech"):
    """
    Check if two texts are reasonably well-aligned translations of each other.
    
    Args:
        source_text (str): The source language text
        target_text (str): The target language text
        source_lang (str): The name of the source language
        target_lang (str): The name of the target language
        
    Returns:
        dict: A dictionary with alignment score and confidence
    """
    try:
        # Create a prompt for the OpenAI model
        prompt = f"""
        Evaluate if these two texts are properly aligned translations:
        
        {source_lang}: {source_text}
        {target_lang}: {target_text}
        
        Return a JSON object with:
        1. "alignment_score" (0.0-1.0) where 1.0 means perfect alignment
        2. "confidence" (0.0-1.0) indicating your confidence in this assessment
        3. "explanation" - a brief explanation of the score
        
        Only include translations that accurately convey the same information. Do not consider stylistic differences as misalignment.
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a bilingual translation expert in evaluating text alignment quality."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Ensure valid values
        alignment_score = max(0.0, min(1.0, float(result.get("alignment_score", 0))))
        confidence = max(0.0, min(1.0, float(result.get("confidence", 0))))
        explanation = result.get("explanation", "No explanation provided")
        
        return {
            "alignment_score": alignment_score,
            "confidence": confidence,
            "explanation": explanation,
            "is_aligned": alignment_score >= 0.7  # Consider 0.7+ as reasonably aligned
        }
        
    except Exception as e:
        logging.error(f"Error checking translation alignment: {str(e)}")
        return {
            "alignment_score": 0.0,
            "confidence": 0.0,
            "explanation": f"Error: {str(e)}",
            "is_aligned": False
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
    import random
    
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
            
        result = check_translation_alignment(source, target)
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
    good_pair = (
        "The quick brown fox jumps over the lazy dog.",
        "Rychlá hnědá liška skáče přes líného psa."
    )
    
    # Bad alignment example
    bad_pair = (
        "The quick brown fox jumps over the lazy dog.",
        "Dnes je krásný den a svítí slunce."  # "Today is a beautiful day and the sun is shining."
    )
    
    print("Testing good alignment:")
    good_result = check_translation_alignment(*good_pair)
    print(json.dumps(good_result, indent=2))
    
    print("\nTesting bad alignment:")
    bad_result = check_translation_alignment(*bad_pair)
    print(json.dumps(bad_result, indent=2))

if __name__ == "__main__":
    test_alignment_check()