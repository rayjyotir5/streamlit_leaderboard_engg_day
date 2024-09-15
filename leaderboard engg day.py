import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

API_TOKEN = 'tfp_A17xvd2NHQdM7YAtc8H5p3Zu5x7xdyMpzKZPBHCnyS7V_epBmPVfapHkE'#os.getenv('TYPEFORM_API_TOKEN')
FORM_ID = 'K1A2k24R'#os.getenv('TYPEFORM_FORM_ID')

BASE_URL = 'https://api.typeform.com'

def get_responses():
    url = f"{BASE_URL}/forms/{FORM_ID}/responses"
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}'
    }
    
    params = {
        'page_size': 100,
        'completed': 'true',
        'page': 1
    }
    
    all_responses = []
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    
    while True:
        try:
            response = http.get(url, headers=headers, params=params, verify=False)
            response.raise_for_status()
            
            data = response.json()
            all_responses.extend(data.get('items', []))
            
            if data.get('total_items', 0) <= len(all_responses):
                break
            
            params['page'] += 1
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred while fetching responses: {e}")
            st.warning("Retrying in 5 seconds...")
            time.sleep(5)
            continue
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            break

    return all_responses

def extract_first_last_name(first_name, last_name):
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    return "Anonymous"

def format_time_taken(seconds):
    time_taken = timedelta(seconds=round(seconds))
    minutes, seconds = divmod(time_taken.seconds, 60)
    if minutes == 0:
        return f"{seconds} seconds"
    else:
        minute_text = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {minute_text} {seconds} seconds"

def extract_data(response):
    try:
        score = response.get('calculated', {}).get('score', 0)
        
        answers = response.get('answers', [])
        first_name = None
        last_name = None
        for answer in answers:
            field_ref = answer.get('field', {}).get('ref', '')
            if field_ref == 'dafbcce9-8984-49b5-bf8f-d4ff550a891d':
                first_name = answer.get('text', '')
            elif field_ref == '2579b945-ae4d-412a-bda6-68830c18e72e':
                last_name = answer.get('text', '')
        
        name = extract_first_last_name(first_name, last_name)
        
        landed_at = datetime.fromisoformat(response['landed_at'].replace('Z', '+00:00'))
        submitted_at = datetime.fromisoformat(response['submitted_at'].replace('Z', '+00:00'))
        time_taken_seconds = (submitted_at - landed_at).total_seconds()
        
        return {
            'Name': name,
            'Score': score,
            'Time Taken': format_time_taken(time_taken_seconds),
            'Time in Seconds': time_taken_seconds
        }
    except KeyError as e:
        st.warning(f"Error processing response: {e}")
        return None

def update_dashboard():
    responses = get_responses()
    data = [extract_data(response) for response in responses]
    data = [d for d in data if d is not None]
    
    df = pd.DataFrame(data)
    
    df_sorted = df.sort_values(by=['Score', 'Time in Seconds'], ascending=[False, True])
    df_sorted = df_sorted.drop(columns=['Time in Seconds'])
    
    df_sorted = df_sorted.reset_index(drop=True)
    df_sorted.index += 1
    
    return df_sorted

def set_custom_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

        * {
            font-family: 'Montserrat', sans-serif !important;
        }
        .leaderboard-table {
            font-size: 25px !important;
            font-weight: bold !important;
            width: 100%;
            border-collapse: separate;
            border-spacing: 15px;
            color: white;
            background-color: rgba(14,17,23,255);
        }
        .leaderboard-table th, .leaderboard-table td {
            padding: 12px;
            text-align: center;
            border: none;
            border-radius: 10px;
            background-color: #222;
        }
        .leaderboard-table th {
            font-size: 25px !important;
            font-weight: 900 !important;
            background-color: #333;
        }
        .stDataFrame table {
            border: none !important;
        }
        .leaderboard-table tr {
            border: none !important;
        }
        .stDataFrame {
            border: none !important;
        }
        .stDataFrame > div {
            border: none !important;
        }
        .stDataFrame > div > div {
            border: none !important;
        }
        .element-container {
            margin: 0 !important;
            padding: 0 !important;
        }
        .stDataFrame table {
            width: 100% !important;
        }
        body {
            background-color: rgba(14,17,23,255);
        }
        .stApp {
            background-color: rgba(14,17,23,255);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def main():
    st.set_page_config(layout="wide")

    set_custom_style()
    
    st.markdown("<h1 style='text-align: center;'><span style='font-size: 43px;'>⭐</span><span style='font-size: 80px;'>🌟</span><span style='font-size: 43px;'>⭐</span></h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; white-space: nowrap; font-family: "Montserrat", sans-serif;'>
        <span style='font-size: 60px; color: #09C4B6; vertical-align: middle; margin: 0 20px; font-weight: bold;'>Linecraft Quiz - Leaderboard</span>
    </div>
    """, unsafe_allow_html=True)

    if 'last_update' not in st.session_state:
        st.session_state.last_update = 0

    leaderboard_placeholder = st.empty()

    while True:
        current_time = time.time()
        if current_time - st.session_state.last_update >= 15:
            df_sorted = update_dashboard()
            st.session_state.last_update = current_time

            with leaderboard_placeholder.container():
                table_html = df_sorted.to_html(classes='leaderboard-table', index=True, escape=False).replace('border="1"','border="0"')
                st.markdown(table_html, unsafe_allow_html=True)

        time.sleep(1)

if __name__ == "__main__":
    main()