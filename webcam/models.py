from django.db import models
from django.contrib.gis.db import models as gis_models

class IntersectionModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="Id")
    name = models.CharField(unique=True, max_length=100, default="", null=False, name="IntersectionName")
    address = models.CharField(unique=True, max_length=100, default="", null=False, name="IntersectionAddress")
    country = models.CharField(max_length=100, default="", null=False, name="IntersectionCountry")
    city = models.CharField(max_length=100, default="", null=False, name="IntersectionCity")
    coordXY =  gis_models.PointField(srid=4326)
    entriesNumber = models.IntegerField()
    individualToggle = models.BooleanField(default=False)
    is_smart_algorithm_enabled = models.BooleanField(default=True, name="IntersectionIsSmartAlgorithmEnabled")

class IntersectionEntryModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="Id")
    intersectionId = models.ForeignKey(
        IntersectionModel,
        related_name='entries',
        on_delete=models.CASCADE
    )

    entry_number = models.PositiveIntegerField()

    coordinates1 = gis_models.PointField(srid=4326)
    coordinates2 = gis_models.PointField(srid=4326)

    traffic_score = models.IntegerField()


class UserProfileModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, name="Id")
    fullName = models.CharField(max_length=100, default="", null=False, name="FullName")
    city = models.CharField(max_length=100, default="", null=False, name="City")
    country = models.CharField(max_length=100, default="", null=False, name="Country")
    county_or_state = models.CharField(max_length=100, default="", null=False, name="County/State")
    phone = models.CharField(max_length=15, default="", null=False, name="Phone")