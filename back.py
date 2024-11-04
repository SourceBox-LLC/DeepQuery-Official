import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_access_token(email, password):
    """Authenticate and get access token from LLM API."""
    LLM_API_URL = os.getenv("LLM_API_URL")
    logger.debug(f"Attempting to authenticate user: {email}")
    try:
        response = requests.post(f"{LLM_API_URL}/login", json={"email": email, "password": password})
        logger.debug(f"Login response status: {response.status_code}")
        response.raise_for_status()  # Raises an HTTPError for bad responses
        access_token = response.json().get("access_token")
        logger.debug(f"Access token received: {access_token}")
        return access_token
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during login: {e}")
        if e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        return None

def send_to_llm_api(user_message, history, pack_id, access_token):
    """Send query to LLM API."""
    LLM_API_URL = os.getenv("LLM_API_URL")
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "user_message": user_message,
        "pack_id": pack_id,
        "history": history
    }
    logger.debug(f"Preparing to send payload: {payload} with headers: {headers}")
    try:
        response = requests.post(f"{LLM_API_URL}/deepquery", json=payload, headers=headers)
        logger.debug(f"DeepQuery response status: {response.status_code}")
        response.raise_for_status()
        response_data = response.json()
        logger.debug(f"Response data: {response_data}")
        return response_data
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return {"error": f"HTTP error occurred: {http_err} - Response: {response.text}"}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        if req_err.response is not None:
            logger.error(f"Response content: {req_err.response.text}")
            return {"error": f"Request error occurred: {req_err} - Response: {req_err.response.text}"}
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return {"error": f"Other error occurred: {err}"}

def fetch_user_packs(access_token):
    """Fetch user packs from the API."""
    API_URL = os.getenv("API_URL")
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{API_URL}/packman/list_packs", headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        packs = response.json()  # Directly use the response as a list

        # Log only the number of packs and their IDs
        pack_ids = [pack['id'] for pack in packs]
        logger.debug(f"Fetched {len(packs)} packs with IDs: {pack_ids}")

        return packs
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        if req_err.response is not None:
            logger.error(f"Response content: {req_err.response.text}")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
    return []

if __name__ == "__main__":
    # Get access token
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    access_token = get_access_token(email, password)

    if not access_token:
        print("Failed to authenticate. Exiting.")
        exit(1)

    # Get user input
    user_message = input("Enter your message: ")
    history = input("Enter your history: ")
    pack_id = input("Enter your pack_id: ")

    # Log user inputs
    logger.debug(f"User message: {user_message}")
    logger.debug(f"History: {history}")
    logger.debug(f"Pack ID: {pack_id}")

    # Call the LLM API
    result = send_to_llm_api(user_message, history, pack_id, access_token)
    print("Chatbot Result:", result)