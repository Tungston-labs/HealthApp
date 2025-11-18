# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from .models import Trainer
# from accounts.models import User

# @receiver(post_save, sender=Trainer)
# def create_user_on_approval(sender, instance, created, **kwargs):
#     # Run only when status changes to approved
#     if instance.status == 'approved' and instance.user is None:
#         password = instance.password  # use trainer-set password

#         user = User.objects.create_user(
#             email=instance.email,
#             phno=instance.phno,
#             password=password,
#             role='trainer',
#             name=instance.name
#         )
#         instance.user = user
#         instance.save()

# @receiver(post_delete, sender=Trainer)
# def delete_user_on_trainer_delete(sender, instance, **kwargs):
#     if instance.user:
#         instance.user.delete()
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trainer, TrainerAvailability

@receiver(post_save, sender=Trainer)
def create_trainer_availability(sender, instance, created, **kwargs):
    if instance.status == "approved":
        TrainerAvailability.objects.get_or_create(trainer=instance)
