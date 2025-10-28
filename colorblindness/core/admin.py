from django.contrib import admin

from .models import Simulation, ColorDetection, TestQuestion, TestResult

# Register your models here.
@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ("user", "blindness_type", "original_image", "transformed_image", "created_at")
    list_filter = ("blindness_type", "created_at")
    search_fields = ("user__username",)

@admin.register(ColorDetection)
class ColorDetectionAdmin(admin.ModelAdmin):
    list_display = ("user", "detected_color", "rgb_value", "hex_value", "image", "created_at")
    list_filter = ("detected_color", "created_at")
    search_fields = ("user__username", "detected_color")


admin.site.register(TestQuestion)
admin.site.register(TestResult)
