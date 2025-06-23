from django.contrib import admin

from webcam.models import IntersectionModel, UserProfileModel, IntersectionEntryModel, \
    AvgVehicleThroughputDataPointModel, AvgWaitingTimeDataPointModel

admin.site.register(IntersectionModel)
admin.site.register(IntersectionEntryModel)
admin.site.register(AvgWaitingTimeDataPointModel)
admin.site.register(AvgVehicleThroughputDataPointModel)

admin.site.register(UserProfileModel)
