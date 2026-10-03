from django.contrib import admin
from warehouse.models import MovementType, ItemType, Warehouse, Plant, UnitType


@admin.register(MovementType)
class MovementTypeAdmin(admin.ModelAdmin):
    list_display = ('mvt_code', 'mvt_name', 'mvt_vn_name', 'desc')

@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ('type_code', 'type_name', 'type_vn_name', 'desc')

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('plant_code', 'plant_name')

@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'unit_name', 'desc')