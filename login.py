import os
from huggingface_hub import login

# Read the token from the environment variable
token = os.getenv("HF_TOKEN")

if not token:
    print("Error: HF_TOKEN environment variable not set.")
else:
    try:
        login(token=token)
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
