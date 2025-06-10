from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class IntersectionModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="id", null=False, unique=True, default="")
    name = models.CharField(unique=True, max_length=100, default="", null=False, name="name")
    address = models.CharField(unique=True, max_length=100, default="", null=False, name="address")
    country = models.CharField(max_length=100, default="", null=False, name="country")
    city = models.CharField(max_length=100, default="", null=False, name="city")
    coordinates =  gis_models.PointField(srid=4326, name="coordinates", null=True)
    entries_number = models.IntegerField(name="entries_number", null=True)
    individual_toggle = models.BooleanField(default=False, name="individual_toggle")
    smart_algorithm_enabled = models.BooleanField(default=True, name="smart_algorithm_enabled")

class IntersectionEntryModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="id", null=False, unique=True, default="")
    intersection = models.ForeignKey(
        IntersectionModel,
        to_field='id',
        on_delete=models.CASCADE,
        name="intersection",
        null=True,
        related_name="entries",
    )
    entry_number = models.PositiveIntegerField(name="entry_number", null=True)
    coordinates1 = gis_models.PointField(srid=4326, name="coordinates1", null=True)
    coordinates2 = gis_models.PointField(srid=4326, name="coordinates2", null=True)
    traffic_score = models.IntegerField(name="traffic_score", default=0)

class UserProfileModel(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        name="user",
        primary_key=True,
        null=False,
        unique=True,
        default="",
        related_name="profile",
    )
    city = models.CharField(max_length=100, default="", null=False, name="city")
    country = models.CharField(max_length=100, default="", null=False, name="country")
    county_or_state = models.CharField(max_length=100, default="", null=False, name="county_or_state")
    phone = models.CharField(max_length=15, default="", null=False, name="phone")

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfileModel.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
