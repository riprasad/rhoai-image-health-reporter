import argparse
import datetime
import requests
from typing import Any, Dict, List, Tuple
# local packages
from logger import logger
from util import util
from mailer import mailer



LOGGER = logger.getLogger(__name__)
CONFIG_FILE = "config.yaml"
SERVER_URL = "https://catalog.redhat.com/api/containers/v1"
REGISTRY = "registry.access.redhat.com"
EMAIL_TEMPLATE_FILE_PATH="mailer/template/image_health_report.html"





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




def prepare_health_report(product_listing_id: str) -> Tuple[Dict[str, List[Any]], Dict[str, int]]:
    """
    Generates a comprehensive health report for the specified product listing.

    This function retrieves all repositories associated with the given product listing ID and
    subsequently gathers health information for each image within these repositories. It then
    filters out non-supported versions and compiles two data dictionaries:

    - grade_report: Groups images across repositories by their health grades. Each key represents a 
    health grade (A-F), and the value is a list of images with that grade, including details such as
    repository name, supported stream tags, image tag, image grade, next drop date and days remaining.

    - grade_count: Provides a summary of the number of images assigned to each health grade (A-F).
    Each key represents a grade, and the value is the count of images with that grade.
    """
    
    # Initializing empty dictionaries to store details by health grade.
    grade_report: Dict[str, list[Any]] = {grade: [] for grade in "FEDCBA"}
    grade_count: Dict[str, int] = {grade: 0 for grade in "ABCDEF"}
    
    
    
    LOGGER.info(f"Fetching repositories data for product listing id: {product_listing_id}")
    product_listing_data = get_repositories_and_supported_streams(product_listing_id)
    LOGGER.debug(f"  Repository Data: {product_listing_data}")
    
    if product_listing_data.get("data"):
        
        # Extract the list of repositories from the "data" key in the dictionary
        repositories = product_listing_data.get("data")
        LOGGER.info(f"   Success: Fetched data for {len(repositories)} repositories.")
        
        
        LOGGER.info("Fetching health data for images across repositories.")
        for repo in repositories:
            repository = repo.get("repository")
            content_stream_tags = repo.get("content_stream_tags")
            
            all_image_grades = get_image_grades(repository)
            LOGGER.debug(f"  Health Grades For All Images In The Repository '{repository}': {all_image_grades}")
            
            if all_image_grades:
                LOGGER.info(f"   Success: {repository}")
                
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
                 LOGGER.error(f"An error occured while fetching health grade of images in repository '{repository}'.")
                 exit(1)
            
    else:
        LOGGER.error(f"An error occured while fetching the data for product listing id '{product_listing_id}'.")
        exit(1)
        
    return grade_report, grade_count




def main():
    
    # Parse the command-line argument --send-mail. If provided, send_mail is set to True; otherwise, it's False.
    parser = argparse.ArgumentParser()
    parser.add_argument('--send-mail', action='store_true', help='Flag to indicate whether to send mail.', dest='send_mail')
    args = parser.parse_args()
    send_mail = args.send_mail
    
    configs = util.get_configs(CONFIG_FILE)
    LOGGER.debug(f"Configs: {configs}")
    for config in configs:
        product_listing_name = config.get('name')
        product_listing_id = config.get('product-listing-id')
        email_recipients = config.get('email-recipients')
        email_subject = f"[{product_listing_name}] Daily Image Health Report: {datetime.datetime.now(datetime.timezone.utc).strftime('%d-%m-%Y')}"
    
        LOGGER.info("=======================================================================================")
        LOGGER.info(f"Generating Image Health Report For Product: {product_listing_name}")
        LOGGER.info("=======================================================================================")
        grade_report, grade_count = prepare_health_report(product_listing_id)
        
        
        LOGGER.info("Data compilation complete. Sorting each grade's list by days_remaining.")
        for grade in grade_report:
            grade_report[grade].sort(key=lambda x: x['days_remaining'])
        LOGGER.debug(f"  Report  : {grade_report}")
        LOGGER.debug(f"  Summary : {grade_count}")
        LOGGER.info("Report Generated Successfully.")
        
        
        LOGGER.info("=======================================================================================")
        LOGGER.info("Sending Report via Email")
        LOGGER.info("=======================================================================================")
        LOGGER.info("Preparing HTML report.")
        rendered_html = util.render_template(EMAIL_TEMPLATE_FILE_PATH, grade_report, grade_count)
        LOGGER.debug(f"  Rendered HTML Report: \n{rendered_html}")
        LOGGER.info("   Success: HTML report generated successfully.")
            
        if send_mail:
            LOGGER.info("Sending email...")
            mailer.send_html_email(subject=email_subject, toaddrs=email_recipients, rendered_html=rendered_html)
            LOGGER.info("Email sent successfully. Email's Summary:")
        else:
            LOGGER.info(f"Skipping email dispatch as 'send_mail' parameter is set to '{send_mail}'.")
            LOGGER.info("Email summary:")
        
        LOGGER.info(f"   Subject    : {email_subject}")
        LOGGER.info(f"   Recipients : {email_recipients}")
    
    
    
    
    
    
if __name__ == '__main__':
    main()