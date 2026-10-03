from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, Unit, UserType, HomePageOption
from .forms import CustomUserChangeForm, CustomUserCreationForm

admin.site.register(HomePageOption)

@admin.register(Unit)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ('unitId', 'unitName', 'isValid', 'update_at', 'update_by')


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ('type_id', 'type_name', 'update_at', 'update_by')


class CustomUserAdmin(UserAdmin):
    # The forms to add and change user instances

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference the removed 'username' field
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name',
                                         'mobile_number')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')}
         ),
    )
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'first_name', 'last_name',
                    'mobile_number', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'mobile_number',)
    ordering = ('username',)


admin.site.register(CustomUser, CustomUserAdmin)
