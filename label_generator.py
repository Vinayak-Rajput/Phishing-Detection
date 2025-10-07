import pandas as pd
import os

# --- Configuration ---
FEATURES_INPUT = 'data/processed/url_features.csv'
LABELED_OUTPUT = 'data/processed/labeled_features.csv'

def apply_labeling_rules(df):
    """Applies a set of heuristics to weakly label the data."""
    print("--> Applying weak supervision rules to generate labels...")
    
    df['is_phishing'] = 0
    
    # FIX: Replaced inplace=True to avoid the FutureWarning
    df['domain_age_days'] = df['domain_age_days'].fillna(9999)

    # --- Rule 1: High Suspicion (Very New and Random) ---
    condition1 = (df['domain_age_days'] < 10) & (df['domain_entropy'] > 4.1)
    df.loc[condition1, 'is_phishing'] = 1
    print(f"--> Labeled {len(df[condition1])} domains as phishing based on Rule 1 (New & Random).")

    # --- Rule 2: High Suspicion (Lookalike Domain Patterns) ---
    condition2 = (df['hyphens_count'] > 3) | (df['dots_count'] > 4)
    df.loc[condition2, 'is_phishing'] = 1
    print(f"--> Labeled {len(df[condition2])} additional domains as phishing based on Rule 2 (Lookalike Patterns).")

    # --- Rule 3: High Suspicion (Suspect Keywords in Long Domains) ---
    suspect_keywords = ['login', 'secure', 'account', 'update', 'verify', 'bank']
    keyword_regex = '|'.join(suspect_keywords)
    condition3 = (df['url'].str.contains(keyword_regex, case=False)) & (df['url_length'] > 40)
    df.loc[condition3, 'is_phishing'] = 1
    print(f"--> Labeled {len(df[condition3])} additional domains as phishing based on Rule 3 (Keywords in Long URLs).")

    return df

# --- Main execution block ---
if __name__ == "__main__":
    print(f"--> Loading feature set from {FEATURES_INPUT}")
    try:
        features_df = pd.read_csv(FEATURES_INPUT)
    except FileNotFoundError:
        print(f"[!] Error: The input file was not found. Please run feature_extractor.py first.")
        exit()

    labeled_df = apply_labeling_rules(features_df)

    labeled_df.to_csv(LABELED_OUTPUT, index=False)
    
    print("\n[+] Label generation complete!")
    print(f"--> Results saved to {LABELED_OUTPUT}")
    
    print("\n--- Label Distribution ---")
    print(labeled_df['is_phishing'].value_counts())