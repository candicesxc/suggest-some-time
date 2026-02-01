def get_calendar_service():
    # 
    # ... other code ...
    
    creds_data = {}  # Ensure creds_data is defined or fetched correctly
    creds = Credentials(token=creds_data.get('token'), refresh_token=creds_data.get('refresh_token'), token_uri=creds_data.get('token_uri', 'https://oauth2.googleapis.com/token'), client_id=creds_data.get('client_id'), client_secret=creds_data.get('client_secret'))
    
    # ... other code ...