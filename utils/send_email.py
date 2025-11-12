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

    if email_type == 'user_registered_notification':
        subject = "New Ambassador registered by you referral code"
        html_content = render_to_string(
            "emails/reset_password.html",
            {
                "user": user,
                "reset_url": url,
                "current_year": datetime.now().year,
            }
        )

    if email_type == 'stripe_onboarding':
        subject = "Complete your Stripe onboarding"
        html_content = render_to_string(
            "emails/stripe_onboarding.html",
            {
                "user": user,
                "onboarding_url": url,
            }
        )
    # Build email
    email = EmailMessage(subject, html_content, from_email, to)
    email.content_subtype = "html"  # Important → tells Django it's HTML
    email.send()


def send_notification_email(to_user, notification_object, notification_type):

    from_email = settings.DEFAULT_FROM_EMAIL
    to = [to_user.email]

    if notification_type == "user":
        subject = "New Ambassador registered by you referral code"
        html_content = render_to_string(
            "emails/user_registered_notification.html",
            {
                "user": notification_object,
                "inviter_user": to_user,
            }
        )

    if notification_type == "prospect":
        subject = "Your Ambassador register the Prospect"
        html_content = render_to_string(
            "emails/prospect_registered_notification.html",
            {
                "prospect": notification_object,
                "inviter_user": to_user,
            }
        )
    # Build email
    email = EmailMessage(subject, html_content, from_email, to)
    email.content_subtype = "html"  # Important → tells Django it's HTML
    email.send()
