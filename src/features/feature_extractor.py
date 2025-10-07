import pandas as pd
import os
from urllib.parse import urlparse
import math
import whois # NEW: Import for WHOIS lookups
from tqdm import tqdm # NEW: Import for progress bar

# Initialize tqdm for pandas
tqdm.pandas()

# --- Configuration ---
CT_LOGS_INPUT = 'data/raw/discovered_urls.txt'
TYPOSQUAT_INPUT = 'data/raw/typosquat_domains.txt'
FEATURES_OUTPUT = 'data/processed/url_features.csv'

def load_domains_from_file(file_path):
    """Loads a list of domains from a text file."""
    if not os.path.exists(file_path):
        print(f"[!] Warning: Input file not found at {file_path}. Skipping.")
        return []
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_domain_from_url(url):
    """Extracts the domain/hostname from a full URL."""
    try:
        if '://' not in url:
            url = 'http://' + url
        parsed_url = urlparse(url)
        return parsed_url.hostname or ''
    except Exception:
        return ''

# --- Feature Extraction Functions ---

def calculate_entropy(text):
    if not text: return 0.0
    prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy

def get_creation_date(domain):
    """
    NEW: Performs a WHOIS lookup to find the domain's creation date.
    Returns NaT (Not a Time) on failure.
    """
    try:
        w = whois.whois(domain)
        # whois can return a list of dates, so we take the first if it's a list
        if isinstance(w.creation_date, list):
            return w.creation_date[0]
        return w.creation_date
    except Exception:
        return pd.NaT # Return pandas' Not a Time for missing values

# --- Main execution block ---
if __name__ == "__main__":
    print("--> Starting feature extraction process...")
    ct_domains = load_domains_from_file(CT_LOGS_INPUT)
    typo_domains = load_domains_from_file(TYPOSQUAT_INPUT)
    all_domains = sorted(list(set(ct_domains + typo_domains)))
    
    if not all_domains:
        print("[!] No domains found in source files. Exiting.")
    else:
        print(f"--> Loaded a total of {len(all_domains)} unique domains.")
        df = pd.DataFrame(all_domains, columns=['url'])

        print("--> Extracting URL-based, Lexical, and Domain-based features...")
        
        # --- Basic URL/Domain Features ---
        df['domain'] = df['url'].apply(get_domain_from_url)
        # Drop any rows where we couldn't parse the domain
        df.dropna(subset=['domain'], inplace=True)
        df = df[df['domain'] != '']

        # --- WHOIS Features (This part will be slow) ---
        print("[*] Performing WHOIS lookups to get creation dates. This will take a while...")
        df['creation_date'] = df['domain'].progress_apply(get_creation_date)
        
        # --- Calculate Domain Age ---
        # Convert creation_date to datetime objects, coercing errors
        df['creation_date'] = pd.to_datetime(df['creation_date'], errors='coerce')
        # Calculate age in days from today
        df['domain_age_days'] = (pd.to_datetime('today') - df['creation_date']).dt.days

        # --- Save results ---
        os.makedirs(os.path.dirname(FEATURES_OUTPUT), exist_ok=True)
        df.to_csv(FEATURES_OUTPUT, index=False)

        print(f"\n[+] Feature extraction complete!")
        print(f"--> Results saved to {FEATURES_OUTPUT}")
        print("\n--- Feature DataFrame Head (sample) ---")
        print(df[['domain', 'creation_date', 'domain_age_days']].head())