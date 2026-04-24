import os
import re
import pandas as pd
import phonenumbers
from flask import Flask, request, jsonify, send_file, render_template_string

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Disposable email domains for bounce heuristic
DISPOSABLE_DOMAINS = {'mailinator.com', '10minutemail.com', 'guerrillamail.com', 'tempmail.com', 'yopmail.com'}

def is_high_bounce_risk(email):
    if not isinstance(email, str):
        return True
    email = email.strip()
    # Basic regex for email validation
    if not re.match(r"^[\w\.\+\-]+\@[\w\-]+\.[a-zA-Z]{2,}$", email):
        return True
    # Domain check for disposable emails
    domain = email.split('@')[-1].lower()
    if domain in DISPOSABLE_DOMAINS:
        return True
    return False

def standardize_phone(phone):
    if pd.isna(phone):
        return ""
    try:
        # Parse phone number, assuming US region as default if no country code is provided
        parsed = phonenumbers.parse(str(phone), "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return str(phone).strip()

@app.route('/')
def index():
    index_path = os.path.join(BASE_DIR, 'index.html')
    with open(index_path, 'r') as f:
        return render_template_string(f.read())

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        try:
            df = pd.read_csv(filepath)
            
            # Ensure required columns exist
            required_cols = ['Name', 'Email', 'Phone Number']
            for col in required_cols:
                if col not in df.columns:
                    return jsonify({'error': f'Missing required column: {col}'}), 400
            
            # 1. Filter out missing emails or phone numbers
            df = df.dropna(subset=['Email', 'Phone Number'])
            df = df[(df['Email'].str.strip() != '') & (df['Phone Number'].astype(str).str.strip() != '')]
            
            # 2. Remove duplicates
            df = df.drop_duplicates(subset=['Name', 'Email', 'Phone Number'], keep='first')
            
            # 3. Split Names
            def split_name(name):
                if pd.isna(name):
                    return "", ""
                parts = str(name).strip().split(maxsplit=1)
                if len(parts) == 2:
                    return parts[0], parts[1]
                elif len(parts) == 1:
                    return parts[0], ""
                return "", ""
            
            df[['First Name', 'Last Name']] = df['Name'].apply(lambda x: pd.Series(split_name(x)))
            
            # 4. Standardize Phone Numbers
            df['Phone Number'] = df['Phone Number'].apply(standardize_phone)
            
            # 5. Email Bounce Algorithm
            df['Bounce_Risk'] = df['Email'].apply(is_high_bounce_risk)
            
            deleted_df = df[df['Bounce_Risk'] == True]
            cleaned_df = df[df['Bounce_Risk'] == False].drop(columns=['Bounce_Risk'])
            
            # 6. Sort by Name, Email, Phone Number
            cleaned_df = cleaned_df.sort_values(by=['Name', 'Email', 'Phone Number'])
            
            # Save outputs
            cleaned_filename = 'cleaned_' + file.filename
            deleted_filename = 'deleted_emails_' + file.filename
            
            cleaned_path = os.path.join(OUTPUT_FOLDER, cleaned_filename)
            deleted_path = os.path.join(OUTPUT_FOLDER, deleted_filename)
            
            # Reorder columns to put First Name and Last Name next to Name
            cols = ['Name', 'First Name', 'Last Name', 'Email', 'Phone Number']
            other_cols = [c for c in cleaned_df.columns if c not in cols]
            cleaned_df = cleaned_df[cols + other_cols]
            
            cleaned_df.to_csv(cleaned_path, index=False)
            deleted_df[['Email']].to_csv(deleted_path, index=False)
            
            return jsonify({
                'message': 'File processed successfully',
                'cleaned_data_url': f'/download/{cleaned_filename}',
                'deleted_emails_url': f'/download/{deleted_filename}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)