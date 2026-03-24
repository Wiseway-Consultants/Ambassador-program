from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from logging import getLogger

from utils.MailChimpAPI import mailchimp_api

User = get_user_model()
logger = getLogger(__name__)


@receiver(post_save, sender=User)
def trigger_new_user_logic(sender, instance, created, **kwargs):
    """
    This function runs EVERY time a User is saved.
    The 'created' boolean tells us if it's a brand new user or just an update.
    """
    if instance.is_active and not instance.in_mail_chimp and "test" not in str(instance.email):
        logger.info("New user created: ", instance.id)
        mailchimp_api.add_contact_to_audience(instance)
        logger.debug("User added to Mailchimp")
        instance.in_mail_chimp = True
        instance.save()
