from warehouse.models import Plant


def plant_context(request):
    if request.user.is_authenticated:
        return {
            "plants": Plant.objects.all(),
            "user_plant": getattr(request.user.plant, "plant_code", request.user.plant)
        }
    return {}
