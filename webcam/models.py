from django.db import models
from django.contrib.gis.db import models as gis_models

class IntersectionModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="id", null=False, unique=True, default="")
    name = models.CharField(unique=True, max_length=100, default="", null=False, name="name")
    address = models.CharField(unique=True, max_length=100, default="", null=False, name="address")
    country = models.CharField(max_length=100, default="", null=False, name="country")
    city = models.CharField(max_length=100, default="", null=False, name="city")
    coordXY =  gis_models.PointField(srid=4326, name="coordinates", null=True)
    entriesNumber = models.IntegerField(name="entries_number", null=True)
    individualToggle = models.BooleanField(default=False, name="individual_toggle")
    enabled_smart_algorithm = models.BooleanField(default=True, name="enabled_smart_algorithm")

class IntersectionEntryModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="id", null=False, unique=True, default="")
    intersectionId = models.ForeignKey(
        IntersectionModel,
        to_field='id',
        on_delete=models.CASCADE,
        name="intersection_id",
        null=True
    )

    entry_number = models.PositiveIntegerField(name="entry_number", null=True)

    coordinates1 = gis_models.PointField(srid=4326, name="coordinates1", null=True)
    coordinates2 = gis_models.PointField(srid=4326, name="coordinates2", null=True)

    traffic_score = models.IntegerField(name="traffic_score", default=0)


class UserProfileModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="id", null=False, unique=True, default="")
    fullName = models.CharField(max_length=100, default="", null=False, name="full_name")
    city = models.CharField(max_length=100, default="", null=False, name="city")
    country = models.CharField(max_length=100, default="", null=False, name="country")
    county_or_state = models.CharField(max_length=100, default="", null=False, name="county_or_state")
    phone = models.CharField(max_length=15, default="", null=False, name="phone")