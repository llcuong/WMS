from django.contrib.auth.backends import ModelBackend, UserModel
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q

from users.models import CustomUser


class EmpNoBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try: #to allow authentication through emp_no or any other field, modify the below statement
            user = UserModel.objects.get(Q(emp_no__iexact=username))
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        except MultipleObjectsReturned:
            return CustomUser.objects.filter(emp_no=username).order_by('id').first()
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def get_user(self, user_id):
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

        return user if self.user_can_authenticate(user) else None