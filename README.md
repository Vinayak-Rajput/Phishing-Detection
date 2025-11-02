# AI-Powered Phishing Detection Engine

A complete machine learning pipeline built in Python to detect and classify phishing URLs in near real-time. This project leverages a multi-source data pipeline and feature engineering to train a predictive model that can identify malicious domains.

*(This project was originally developed as an entry for a national cybersecurity challenge and is now maintained as a personal portfolio project.)*

---

## 🚀 Core Features

* **Multi-Source Data Ingestion**: Gathers potential phishing candidates from:
    * **Live Certificate Transparency (CT) Logs**: Monitors new SSL certificate registrations in real-time.
    * **Typosquatting Generator**: Proactively generates and checks thousands of lookalike domains (e.g., `sbi-bank.com`, `sb1.co.in`) using DNSTwist.
* **Automated Feature Engineering**: Automatically extracts a rich set of features from each domain, including:
    * **Lexical Features**: URL length, hyphen/dot count, and domain entropy (randomness).
    * **Domain-Based Features**: Domain age, creation date, and registration info via **WHOIS** lookups.
* **ML-Powered Classification**: Uses a **Scikit-learn (Random Forest)** model to classify URLs as "Phishing" or "Benign" based on the engineered features.
* **Automated Evidence Collection**: Deploys a **Selenium** headless browser to visit detected phishing sites, capture full-page screenshots, and save them as PDF reports.
* **Weak Supervision**: Implements a weak supervision system to programmatically label the training dataset, enabling rapid model bootstrapping without manual data labeling.

---

## 🛠️ Tech Stack

* **Core Language**: Python 3.10+
* **Machine Learning**: Scikit-learn (RandomForest), Pandas
* **Data Sourcing**: CertStream, DNSTwist, Whois, Requests
* **Web Automation**: Selenium (with Geckodriver)
* **Utility**: Jupyter Lab, Joblib

---

## 🏁 How to Use

### 1. Setup

**Clone the repository and create a virtual environment:**
```bash
git clone [https://github.com/YourUsername/phishing-detection-challenge.git](https://github.com/YourUsername/phishing-detection-challenge.git)
cd phishing-detection-challenge
python -m venv venv
.\venv\Scripts\activate
```
**Install the required dependecies:**
```bash
pip install -r requirements.txt
```
* **Download the WebDriver:** Download the geckodriver for your OS and place geckodriver.exe in the project's root directory.

### 2. Run the Full Pipeline

**Step 1: Gather Data (Optional, can take time)**
Run the data sourcing scripts to populate the `data/raw/` folder.
```bash
# Monitor live CT logs
python src/crawlers/ct_monitor.py

# Generate typosquatted domains (slow)
python src/crawlers/typosquat_generator.py
```

**Step 2: Generate Features (Required)**
This script takes the raw domains, samples them, and performs the slow WHOIS lookups to create the feature set.

```bash
python src/features/feature_extractor.py
```

**Step 3: Auto-Label the Data (Required)**
This applies our weak supervision rules to create the labeled dataset.

```bash
python label_generator.py
```

**Step 4: Train the Model (Required)** 
Run the Jupyter Notebook at notebooks/01-baseline-model-training.ipynb to train and save the model to src/models/.

### 3. Make a Prediction
Use the predict.py script to classify a new, unseen URL.

```bash
python predict.py "[http://sbi-bank-login-update-kjh2.xyz](http://sbi-bank-login-update-kjh2.xyz)"
--> Loading model from src/models/phishing_detector_model.joblib...
[+] Model loaded successfully.
--> Extracting features for: [http://sbi-bank-login-update-kjh2.xyz](http://sbi-bank-login-update-kjh2.xyz)
--> Making a prediction...

--- Prediction Result ---
Verdict: 🔴 PHISHING
Confidence: 51.00%
```

### 4. Capture Evidence
Use the screenshot_tool.py to capture a screenshot of any URL.

```bash
python screenshot_tool.py "[https://www.google.com](https://www.google.com)" "evidences/google_test.pdf"
```
