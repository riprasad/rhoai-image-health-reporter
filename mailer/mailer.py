import yagmail
import os


# Mail Configs    
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# Check if the environment variables are set
if not EMAIL_USER or not EMAIL_PASSWORD:
    raise Exception("Environment variables EMAIL_USER or EMAIL_PASSWORD are not set.")
    
    
def send_html_email(subject: str, toaddrs: list, rendered_html: str):
    """
    Sends an HTML email with the specified subject and recipients.
    """
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD)

    # https://github.com/kootenpv/yagmail/issues/124
    html_report = rendered_html.replace("\n", "")

    # Send the email
    yag.send(to=toaddrs, subject=subject, contents=html_report)