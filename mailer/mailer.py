import yagmail
from jinja2 import Environment, FileSystemLoader
import os

import sys
sys.path.append("..")
import logger

LOGGER = logger.getLogger(__name__)


def render_template(template_file, grade_report, grade_count):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_file)
    return template.render(grade_report=grade_report, grade_count=grade_count)


def send_html_email(subject, toaddrs, template_file, grade_report, grade_count):
    email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    yag = yagmail.SMTP(email, password)

    # Render the HTML template with data
    rendered_html = render_template(template_file, grade_report, grade_count)
    LOGGER.debug(f"\nRendered HTML Report: {rendered_html}")

    # https://github.com/kootenpv/yagmail/issues/124
    html_report = rendered_html.replace("\n", "")

    # Send the email
    yag.send(to=toaddrs, subject=subject, contents=html_report)


