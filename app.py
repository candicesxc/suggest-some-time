# Your current file content with the necessary change made

# import statements
from google.oauth2.credentials import Credentials

# ...

# line 92
credentials = Credentials.from_authorized_user(info) # Removed the scopes parameter

# ...