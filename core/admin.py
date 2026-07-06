from django.contrib import admin
from .models import Metal, Banknote, Location, MetalPhoto, Coin

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")

@admin.register(Metal)
class MetalAdmin(admin.ModelAdmin):
    list_display = ("type", "material", "weight_grams", "acquisition_value", "user", "created_at")
    list_filter = ("type", "material")

@admin.register(Banknote)
class BanknoteAdmin(admin.ModelAdmin):
    list_display = ("currency", "denomination", "quantity", "acquisition_value", "user")

@admin.register(MetalPhoto)
class MetalPhotoAdmin(admin.ModelAdmin):
    list_display = ("metal", "sort_order", "created_at")

@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ("country", "year", "denomination", "currency", "metal", "acquisition_value", "user")
    list_filter = ("country", "metal", "currency")
