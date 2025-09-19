from datetime import datetime

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings



def send_email(user, url, email_type: str = "confirm"):

    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    if email_type == 'confirm':
        subject = "Confirm your SaveFryOil Ambassador account"
        html_content = render_to_string("emails/confirm_email.html", {"user": user, "confirm_url": url})

    if email_type == 'reset':
        subject = "Reset password for your SaveFryOil Ambassador account"
        html_content = render_to_string(
            "emails/reset_password.html",
            {
                "user": user,
                "reset_url": url,
                "current_year": datetime.now().year,
            }
        )
    # Build email
    email = EmailMessage(subject, html_content, from_email, to)
    email.content_subtype = "html"  # Important → tells Django it's HTML
    email.send()
