import yagmail
import os


def send_html_email(subject, toaddrs, rendered_html):
    email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    yag = yagmail.SMTP(email, password)

    # https://github.com/kootenpv/yagmail/issues/124
    html_report = rendered_html.replace("\n", "")

    # Send the email
    yag.send(to=toaddrs, subject=subject, contents=html_report)


