import time
import requests
import json



class Online():

    session = requests.session()

    REQUEST_OK    = 0  # Data can be handled
    REQUEST_RETRY = 1  # Try getting data again
    REQUEST_BAD   = 2  # No point in trying, skip and go to next one

    @staticmethod
    def fetch_web_data(url):
        response = Online.session.get(url, timeout=60*5)

        # Common response if match is yet to exist
        if 'Page Missing' in response.text:
            return Online.REQUEST_RETRY, {}

        # What to do with the data
        status = Online.validate_response(response)
        try: data = json.loads(response.text)
        except: return status, {}

        return status, data


    @staticmethod
    def validate_response(response):
        if response.status_code == 200: return Online.REQUEST_OK     # Ok
        if response.status_code == 400: return Online.REQUEST_BAD    # Unable to process request
        if response.status_code == 401: return Online.REQUEST_BAD    # Need to log in
        if response.status_code == 403: return Online.REQUEST_BAD    # Forbidden
        if response.status_code == 404: return Online.REQUEST_BAD    # Resource not found
        if response.status_code == 405: return Online.REQUEST_BAD    # Method not allowed
        if response.status_code == 407: return Online.REQUEST_BAD    # Proxy authentication required
        if response.status_code == 408: return Online.REQUEST_RETRY  # Request timeout
        if response.status_code == 429: return Online.REQUEST_RETRY  # Too many requests
        if response.status_code == 500: return Online.REQUEST_RETRY  # Internal server error
        if response.status_code == 502: return Online.REQUEST_RETRY  # Bad Gateway
        if response.status_code == 503: return Online.REQUEST_RETRY  # Service unavailable
        if response.status_code == 504: return Online.REQUEST_RETRY  # Gateway timeout


