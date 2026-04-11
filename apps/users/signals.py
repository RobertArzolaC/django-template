import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.users import models
from apps.users.models import User, Account

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_account(sender, instance, created, **kwargs):
    if created:
        try:
            Account.objects.create(user=instance)
            logger.info(
                f"Cuenta creada automáticamente para el usuario: {instance.email}"
            )
        except Exception as e:
            logger.error(
                f"Error al crear cuenta para el usuario {instance.email}: {str(e)}"
            )


########################################
# Migrated from customers app
########################################

@receiver(post_delete, sender=Account)
def remove_account_user(sender, instance, **kwargs):
    user = instance.user
    user.delete()
