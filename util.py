from datetime import datetime
from urllib.parse import urljoin
import logger


LOGGER = logger.getLogger(__name__)



def construct_url(server_url: str, endpoint: str) -> str:
    """
    Constructs a final URL by combining the server URL and the endpoint.
    """
    # Ensure server URL ends with a slash
    if not server_url.endswith('/'):
        server_url += '/'
    
    # Use urljoin to construct the final URL
    final_url = urljoin(server_url, endpoint)
    
    return final_url


def calculate_days_remaining(next_drop_date_str: str) -> int:
    """
    Calculates the number of days remaining from today until the specified date.

    This function accepts a date string in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS+00:00`), 
    parses it to extract the date part, and computes the number of days from the current date 
    to the specified date.
    """
    # Parse the date string including time and timezone
    next_drop_date = datetime.fromisoformat(next_drop_date_str).date()
    today = datetime.today().date()
    days_remaining = (next_drop_date - today).days
    return days_remaining