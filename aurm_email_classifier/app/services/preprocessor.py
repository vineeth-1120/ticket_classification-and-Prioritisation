import re
from langdetect import detect, DetectorFactory

# Set seed for deterministic language detection
DetectorFactory.seed = 0

def clean_html(text: str) -> str:
    """Remove HTML tags."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def remove_signatures_and_headers(text: str) -> str:
    """Remove common email signatures and forwarded headers."""
    lines = text.split('\n')
    cleaned_lines = []
    
    signature_patterns = ['--', 'regards', 'thanks', 'sent from my iphone', 'sent from my android']
    header_patterns = ['forwarded', 'from:', 'to:', 'subject:', 'date:']
    
    for line in lines:
        lower_line = line.strip().lower()
        
        # Stop processing if we hit a likely signature
        if any(lower_line.startswith(sig) for sig in signature_patterns):
            break
            
        # Skip header lines
        if any(lower_line.startswith(header) for header in header_patterns):
            continue
            
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines)

def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces and newlines."""
    # Replace multiple spaces with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def preprocess_email(body: str) -> dict:
    """
    Main preprocessing pipeline:
    1. Strip HTML
    2. Remove signatures and headers
    3. Normalize whitespace
    4. Detect language
    5. Truncate to max 4000 chars
    """
    # 1. Clean HTML
    text = clean_html(body)
    
    # 2. Remove signatures and headers
    text = remove_signatures_and_headers(text)
    
    # 3. Normalize whitespace
    text = normalize_whitespace(text)
    
    # 4. Detect language
    try:
        lang = detect(text) if text else "en"
    except:
        lang = "en"
        
    # 5. Truncate to max 4000 chars (keep beginning and end, ellipsis in middle)
    if len(text) > 4000:
        half = 1998
        text = text[:half] + "..." + text[-half:]
        
    return {
        "cleaned_body": text,
        "language": lang
    }
