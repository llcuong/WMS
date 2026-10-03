import os
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, get_language
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core import validators
from django.contrib.auth.models import BaseUserManager
from django.conf import settings
from django.contrib.auth.models import User, Group

from warehouse.models import Plant


class HomePageOption(models.Model):
    name = models.CharField(max_length=100)
    name_tw = models.CharField(max_length=100)
    name_cn = models.CharField(max_length=100)
    name_vn = models.CharField(max_length=100)
    url_name = models.CharField(max_length=200)
    roles = models.ManyToManyField(Group, blank=True)

    def __str__(self):
        language = get_language()
        field_name = self.name
        if language == 'zh-hant':
            field_name = self.name_tw
        elif language == 'zh-hans':
            field_name = self.name_cn
        elif language == 'vi':
            field_name = self.name_vn
        return field_name


class Unit(models.Model):
    unitId = models.CharField("部門編號", max_length=30, unique=True)
    orgId = models.CharField("組織編號", max_length=30, blank=False, null=False)
    unitName = models.CharField("部門名稱", max_length=30, blank=False, null=False)
    isValid = models.CharField("失效", max_length=1, blank=False, null=False, default=0)
    cost_center = models.CharField("成本中心", max_length=30, blank=True, null=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='unit_manager',
                                null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, editable=True)  # 建立日期
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='unit_create_by')  # 建立者
    update_at = models.DateTimeField(auto_now=True, null=True)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='unit_update_by')

    def __str__(self):
        return self.unitName

class UserType(models.Model):
    type_id = models.IntegerField(primary_key=True)
    type_name = models.CharField(_('類別'), max_length=50)
    create_at = models.DateTimeField(default=timezone.now)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='user_type_create_at')
    update_at = models.DateTimeField(auto_now=True, null=True)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='user_type_update_by')

    def __str__(self):
        return self.type_name


class CustomUserManager(BaseUserManager):

    def _create_user(self, username, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        user = self.model(username=username,
                          is_staff=is_staff,
                          is_active=True,
                          is_superuser=is_superuser,
                          last_login=now,
                          date_joined=now,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        return self._create_user(username, password, True, True,
                                 **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    A fully featured User model with admin-compliant permissions that uses
    a full-length email field as the username.

    Email and password are required. Other fields are optional.
    """
    emp_no = models.CharField(_('emp_no'), max_length=30, blank=False, null=False, unique=True)
    sap_emp_no = models.CharField(_('sap_emp_no'), max_length=30, blank=True, null=True)
    username = models.CharField(_('username'), max_length=30)
    email = models.EmailField(_('email address'), max_length=254, null=True, blank=True)
    user_type = models.ForeignKey(UserType, related_name='user_type', null=True, on_delete=models.DO_NOTHING)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    shot = models.FileField(upload_to='uploads/profile', null=True, blank=True)
    mobile_number = models.CharField(_('mobile number'), max_length=30, blank=True,
                                     help_text=_(
                                         'Required. digits and +-() only.'),
                                     validators=[validators.RegexValidator(r'^[0-9+()-]+$',
                                                                           _('Enter a valid mobile number.'),
                                                                           'invalid')])
    # Admin
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    plant = models.ForeignKey(Plant, related_name='users_plant', on_delete=models.DO_NOTHING, null=True, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='user_manager', null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

        permissions = (
            ('perm_stock', '庫存管理系統權限'),
        )

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s%s' % (self.last_name, self.first_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])




# @receiver(models.signals.post_delete, sender=CustomUser)
# def auto_delete_file_on_delete(sender, instance, **kwargs):
#     if instance.files:
#         if os.path.isfile(instance.files.path):
#             os.remove(instance.files.path)
