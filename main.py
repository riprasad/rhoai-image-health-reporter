from typing import Any, Dict, List
import logger
import requests
import util
from mailer import mailer


LOGGER = logger.getLogger(__name__)

# https://catalog.redhat.com/api/containers/v1/ui/
SERVER_URL = "https://catalog.redhat.com/api/containers/v1"
REGISTRY = "registry.access.redhat.com"



def get_repositories_and_supported_streams(product_listing_id: str) -> Dict[str, Any]:
    """
    Retrieves information about all repositories and their supported stream tags
    for a given product listing ID.
    
    The request includes the following parameters:
    - `include`: Comma-separated list of fields to include in the response.
    - `page_size`: Size of the page that should be returned.
    - `page`: Page number to return.
    """
    endpoint = f"product-listings/id/{product_listing_id}/repositories"
    url = util.construct_url(SERVER_URL, endpoint)

    headers = {"accept": "application/json"}
    
    params = {
        'include': 'data.repository,data.content_stream_tags',
        'page_size': 100,
        'page': 0
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    # Parses the JSON response from the API into a Python dictionary
    data_dict = response.json()
    
    return data_dict
    


def get_image_grades(repository: str) -> List[Dict[str, str]]:
    """
    Fetches and returns the health grade information for all images in the specified repository.
    
    The request includes the following parameters:
    - `include`: Comma-separated list of fields to include in the response.
    """
    endpoint = f"repositories/registry/{REGISTRY}/repository/{repository}/grades"
    url = util.construct_url(SERVER_URL, endpoint)

    headers = {"accept": "application/json"}
    
    params = {
        'include': 'tag,current_grade,next_drop_date'
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    # Parses the JSON response from the API into a Python List
    repository_images_grade = response.json()
    
    return repository_images_grade



def main():
    # TODO - Make it Configurable
    product_listing_id = "63b85b573112fe5a95ee9a3a"
    
    # Initializing empty dictionaries to store details by health grade.
    grade_report: Dict[str, list[Any]] = {grade: [] for grade in "FEDCBA"}
    grade_count: Dict[str, int] = {grade: 0 for grade in "ABCDEF"}
    
    product_listing_data = get_repositories_and_supported_streams(product_listing_id)
    LOGGER.debug(f"Repository Data: {product_listing_data}")
    
    if product_listing_data.get("data"):
        
        # Extract the list of repositories from the "data" key in the dictionary
        repositories = product_listing_data.get("data")
        
        for repo in repositories:
            repository = repo.get("repository")
            content_stream_tags = repo.get("content_stream_tags")
            
            all_image_grades = get_image_grades(repository)
            LOGGER.debug(f"Health Grades For All Images In The Repository '{repository}': {all_image_grades}")
            
            if all_image_grades:
                
                repo_stream_tags = []
                for image in all_image_grades:
                    if image['tag'] in content_stream_tags:
                        # Handle missing next_drop_date by assigning a faux date
                        next_drop_date = image.get('next_drop_date', '2099-12-31T00:00:00+00:00')
                        days_remaining = util.calculate_days_remaining(next_drop_date)
                        repo_stream_tags.append(image['tag'])
                        
                        # Add the processed grade info to the dictionary
                        grade_report[image['current_grade']].append({
                            'repository': repository,
                            'repo_stream_tags': repo_stream_tags,
                            'tag': image['tag'],
                            'current_grade': image['current_grade'],
                            'next_drop_date': next_drop_date.split("T")[0],
                            'days_remaining': days_remaining
                        })
                        
                        # Update the grade count
                        grade_count[image['current_grade']] += 1
    
            else:
                 LOGGER.error(f"An error occured while fetching the health grade of the images in repository '{repository}'.")
                 exit(1)
            
    else:
        LOGGER.error(f"An error occured while fetching the data for product listing id '{product_listing_id}'.")
        exit(1)
    
    
    
    # Sort each grade's list by days_remaining
    for grade in grade_report:
        grade_report[grade].sort(key=lambda x: x['days_remaining'])
        
    LOGGER.info(f"Grade Report: {grade_report}")
    LOGGER.info(f"Grade Count: {grade_count}")
    mailer.send_html_email(
        subject="Your Daily Container Health Report",
        toaddrs=["riprasad@redhat.com"],
        template_file="mailer/template/image_health_report.html",
        grade_report=grade_report,
        grade_count=grade_count,
    )
    
    
    
    
    
if __name__ == '__main__':
    main()