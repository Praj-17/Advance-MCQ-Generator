import openai
import os
from dotenv import load_dotenv
load_dotenv()

def check_openai_api_key(api_key):
    openai.api_key = api_key
    try:
        print(openai.Engine.list())
    except Exception as e:
        print(e)
        return False
    else:
        return True

# Replace os.getenv("OPENAI_KEY") with your OpenAI API key.
# Or you can create a .env file and add OPENAI_KEY=your-api-key
api_key = os.getenv("OPENAI_KEY") 
is_valid = check_openai_api_key(api_key)

if is_valid:
    print("Valid OpenAI API key.")
else:
    print("Invalid OpenAI API key.")
