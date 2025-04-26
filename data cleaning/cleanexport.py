import os
import json
import re
import pandas as pd

# Clean text for title (lowercase + remove punctuation)
def clean_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

# Flatten only author names
def flatten_author_names(authors):
    return '; '.join([a.get('name', '') for a in authors]) if authors else ''

# Flatten only author countries
def flatten_author_countries(authors):
    return '; '.join([a.get('country', '') for a in authors]) if authors else ''

# Extract year as integer
def extract_year(year_str):
    if not year_str:
        return None
    match = re.match(r'(\d{4})', year_str)
    return int(match.group(1)) if match else None

# Flatten keywords
def flatten_keywords(keywords):
    return '; '.join(keywords) if keywords else ''

# Main function to load data and export as CSV
def load_and_export_data(base_path, output_csv):
    records = []
    for root, dirs, files in os.walk(base_path):
        # Only process if current folder is named 'papers'
        if os.path.basename(root) != 'papers':
            continue
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entries = data if isinstance(data, list) else [data]
                    for entry in entries:
                        if not isinstance(entry, dict):
                            continue
                        record = {
                            'url': entry.get('url', ''),
                            'title': clean_text(entry.get('title', '')),
                            'abstract': entry.get('abstract', ''),
                            'citation_count': entry.get('citation_count', ''),
                            'year': entry.get('year', ''),
                            'author_names': flatten_author_names(entry.get('authors', [])),
                            'author_countries': flatten_author_countries(entry.get('authors', [])),
                            'keywords': flatten_keywords(entry.get('keywords', []))
                        }
                        record['year_int'] = extract_year(record['year'])
                        records.append(record)

    # Create DataFrame
    df = pd.DataFrame(records)


    # Export to CSV
    df.to_csv(output_csv, index=False)

# Usage
base_json_path = r'D:\research_trend_analyzer\static'
output_csv = 'cleaned_output.csv'
load_and_export_data(base_json_path, output_csv)
