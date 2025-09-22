from django.contrib import admin
from .models import SensorDevice, SensorData

@admin.register(SensorDevice)
class SensorDeviceAdmin(admin.ModelAdmin):
    list_display = ("device_uid", "company", "is_active", "created_at")
    list_filter = ("company", "is_active")
    search_fields = ("device_uid", "name", "company__name", "company__biz_no")
    readonly_fields = ("api_key", "created_at")

@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ("device", "metric", "value", "ts", "idempotency_key")
    list_filter = ("metric", "device__company")
    search_fields = ("device__device_uid", "metric")
    readonly_fields = ("created_at",)
