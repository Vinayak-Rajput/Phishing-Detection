import pandas as pd
import joblib
import whois
import math
from urllib.parse import urlparse
import argparse
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# --- Configuration ---
MODEL_PATH = 'src/models/phishing_detector_model.joblib'
# IMPORTANT: The order of features must be EXACTLY the same as when the model was trained.
# We get this from our training notebook.
EXPECTED_FEATURES = [
    'url_length', 'domain_length', 'dots_count', 'hyphens_count',
    'special_chars_count', 'domain_entropy', 'domain_age_days'
]

# --- Feature Extraction Functions (copied from our feature extractor) ---

def get_domain_from_url(url):
    try:
        if '://' not in url:
            url = f"http://{url}"
        return urlparse(url).hostname or ''
    except Exception:
        return ''

def get_creation_date(domain):
    try:
        w = whois.whois(domain)
        if w.creation_date:
            return w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
    except Exception:
        pass
    return pd.NaT

def calculate_entropy(text):
    if not text: return 0.0
    prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    return -sum(p * math.log2(p) for p in prob)

def extract_features(url):
    """
    Extracts all necessary features from a single URL and returns a DataFrame.
    """
    features = {}
    
    # URL-based
    features['url_length'] = len(url)
    features['dots_count'] = url.count('.')
    features['hyphens_count'] = url.count('-')
    features['special_chars_count'] = sum(url.count(c) for c in ['@','?','=','&','%','$','#','/'])
    
    # Domain-based
    domain = get_domain_from_url(url)
    if not domain:
        # If we can't get a domain, fill with default values
        features['domain_length'] = 0
        features['domain_entropy'] = 0
        features['domain_age_days'] = -1 # Use -1 or a median for missing age
    else:
        features['domain_length'] = len(domain)
        features['domain_entropy'] = calculate_entropy(domain)
        
        # WHOIS features
        creation_date = get_creation_date(domain)
        if pd.isna(creation_date):
            features['domain_age_days'] = -1 # Use -1 to indicate missing data
        else:
            creation_date_utc = pd.to_datetime(creation_date, errors='coerce', utc=True)
            today_utc = pd.to_datetime('today', utc=True)
            features['domain_age_days'] = (today_utc - creation_date_utc).days

    # Convert dictionary to a pandas DataFrame and ensure column order
    features_df = pd.DataFrame([features])
    return features_df[EXPECTED_FEATURES]

# --- Main Prediction Block ---
if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Predict if a URL is a phishing site.")
    parser.add_argument("url", help="The URL to check.")
    args = parser.parse_args()

    try:
        # Load the trained model
        print(f"--> Loading model from {MODEL_PATH}...")
        model = joblib.load(MODEL_PATH)
        print("[+] Model loaded successfully.")

        # Extract features from the input URL
        print(f"--> Extracting features for: {args.url}")
        url_features = extract_features(args.url)
        
        # Handle potential missing values from feature extraction
        url_features.fillna(-1, inplace=True)

        # Make a prediction
        print("--> Making a prediction...")
        prediction = model.predict(url_features)[0]
        prediction_proba = model.predict_proba(url_features)[0]

        # Display the result
        print("\n--- Prediction Result ---")
        if prediction == 1:
            print("Verdict: 🔴 PHISHING")
            print(f"Confidence: {prediction_proba[1]:.2%}")
        else:
            print("Verdict: 🟢 BENIGN")
            print(f"Confidence: {prediction_proba[0]:.2%}")
    
    except FileNotFoundError:
        print(f"[!] Error: Model file not found at '{MODEL_PATH}'.")
        print("[!] Please run the training notebook first to create and save the model.")
    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}")