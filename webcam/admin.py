from django.contrib import admin

from webcam.models import IntersectionModel, UserProfileModel, IntersectionEntryModel

admin.site.register(IntersectionModel)
admin.site.register(IntersectionEntryModel)
admin.site.register(UserProfileModel)