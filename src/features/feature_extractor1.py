import pandas as pd
import os
from urllib.parse import urlparse
import math
import whois
from tqdm import tqdm
import random

tqdm.pandas()

# --- Configuration ---
CT_LOGS_INPUT = 'data/raw/discovered_urls.txt'
TYPOSQUAT_INPUT = 'data/raw/typosquat_domains.txt'
RAW_FEATURES_OUTPUT = 'data/processed/url_features_raw.csv'
FINAL_FEATURES_OUTPUT = 'data/processed/url_features.csv'
SAMPLE_SIZE = 5000

def get_creation_date(domain):
    """Performs a WHOIS lookup. Returns NaT on any failure."""
    try:
        w = whois.whois(domain)
        if w.creation_date:
            return w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
    except Exception:
        pass
    return pd.NaT

# --- Main execution block ---
if __name__ == "__main__":
    if os.path.exists(RAW_FEATURES_OUTPUT):
        print(f"--> Found existing raw feature file. Loading from {RAW_FEATURES_OUTPUT}")
        df = pd.read_csv(RAW_FEATURES_OUTPUT)
    else:
        # Code to load domains and perform WHOIS lookups
        print("--> No raw feature file found. Starting data acquisition...")
        ct_domains = [line.strip() for line in open(CT_LOGS_INPUT, 'r') if line.strip()] if os.path.exists(CT_LOGS_INPUT) else []
        typo_domains = [line.strip() for line in open(TYPOSQUAT_INPUT, 'r') if line.strip()] if os.path.exists(TYPOSQUAT_INPUT) else []
        all_domains = sorted(list(set(ct_domains + typo_domains)))
        
        if not all_domains:
            print("[!] No domains in source files. Exiting.")
            exit()

        print(f"--> Loaded a total of {len(all_domains)} unique domains.")
        if len(all_domains) > SAMPLE_SIZE:
            print(f"--> Taking a random sample of {SAMPLE_SIZE} domains.")
            all_domains = random.sample(all_domains, SAMPLE_SIZE)
        
        df = pd.DataFrame(all_domains, columns=['url'])
        df['domain'] = df['url'].apply(lambda x: urlparse(f"http://{x}").hostname or '')
        df.dropna(subset=['domain'], inplace=True)
        df = df[df['domain'] != '']

        print(f"[*] Performing WHOIS lookups on {len(df)} domains...")
        df['creation_date'] = df['domain'].progress_apply(get_creation_date)
        
        print(f"--> Saving raw WHOIS results to {RAW_FEATURES_OUTPUT}...")
        df.to_csv(RAW_FEATURES_OUTPUT, index=False)

    print("\n--> Starting fast data processing...")
    
    # All Feature Calculations
    df['url_length'] = df['url'].apply(len)
    df['domain_length'] = df['domain'].apply(len)
    df['dots_count'] = df['url'].apply(lambda x: x.count('.'))
    df['hyphens_count'] = df['url'].apply(lambda x: x.count('-'))
    df['special_chars_count'] = df['url'].apply(lambda x: sum(x.count(c) for c in ['@','?','=','&','%','$','#','/']))
    
    def calculate_entropy(text):
        if not text: return 0.0
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        return -sum(p * math.log2(p) for p in prob)
    df['domain_entropy'] = df['domain'].apply(calculate_entropy)

    df['creation_date'] = pd.to_datetime(df['creation_date'], errors='coerce', utc=True)
    today_utc = pd.to_datetime('today', utc=True)
    df['domain_age_days'] = (today_utc - df['creation_date']).dt.days

    df.to_csv(FINAL_FEATURES_OUTPUT, index=False)
    print(f"\n[+] Feature extraction complete! Final results saved to {FINAL_FEATURES_OUTPUT}")