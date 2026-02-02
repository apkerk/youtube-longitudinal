import os
import yaml
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

def load_config(config_path='config/config.yaml'):
    """Load configuration from YAML file."""
    # Go up one level from src/ to project root if needed, or assume running from root
    # better to check relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_config_path = os.path.join(base_dir, config_path)
    
    with open(abs_config_path, 'r') as f:
        return yaml.safe_load(f)

def get_authenticated_service(api_key=None):
    """Builds and returns the YouTube Data API service."""
    if not api_key:
        config = load_config()
        api_key = config.get('api_key')
        
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("API Key is missing or invalid in config.yaml")
        
    return build('youtube', 'v3', developerKey=api_key)

def execute_request(request, max_retries=5):
    """Executes an API request with exponential backoff for rate limits."""
    retries = 0
    while retries < max_retries:
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status in [403, 429, 500, 503]:
                # Quota exceeded or server error
                sleep_time = (2 ** retries) + (time.time() % 1) # Jitter
                print(f"API Error {e.resp.status}: Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                retries += 1
            else:
                raise e
    raise Exception(f"Failed after {max_retries} retries.")

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
