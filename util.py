import logger
from urllib.parse import urljoin


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
