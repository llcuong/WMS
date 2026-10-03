from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate

from warehouse.models import Plant
from .models import *
from django.utils.translation import gettext_lazy as _
 # extend Django's built-in UserCreationForm and UserChangeForm to
 # remove the username field (and optionally add any others that are
 # required)

class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """

    def __init__(self, *args, **kargs):
        super(CustomUserCreationForm, self).__init__(*args, **kargs)


    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserChangeForm(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    def __init__(self, *args, **kargs):
        super(CustomUserChangeForm, self).__init__(*args, **kargs)

    class Meta:
        model = CustomUser
        fields = '__all__'

# ======================================================
 # Forms for users themselves edit their profiles
 # ======================================================
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Fieldset, HTML, Field
from .models import CustomUser

class CurrentCustomUserForm(forms.ModelForm):
    user_type = forms.ModelChoiceField(label=_('user_type'), queryset=UserType.objects.all(), widget=forms.Select(
        attrs={'class': "form-select"}))
    is_active = forms.BooleanField(label=_('active'), initial=True, required=False, widget=forms.CheckboxInput(attrs={'class': "form-check-input"}))
    password1 = forms.CharField(label=_('password'), required=False, widget=forms.PasswordInput(attrs={'placeholder': _('Please type the password')}))
    password2 = forms.CharField(label=_('confirm_password'), required=False, widget=forms.PasswordInput(attrs={'placeholder': _('Please type the login password again')}))
    emp_no = forms.CharField(label=_('emp_no'), widget=forms.TextInput(attrs={'placeholder': _('emp_no')}))
    sap_emp_no = forms.CharField(label=_('sap_emp_no'), widget=forms.TextInput(attrs={'placeholder': _('sap_emp_no')}), required=False)
    username = forms.CharField(label=_('name'))
    plant = forms.ModelChoiceField(label=_('plant'), queryset=Plant.objects.all(), widget=forms.Select(
        attrs={'class': "form-select"}))

    class Meta:
        model = CustomUser
        fields = ('emp_no', 'username', 'last_name', 'first_name', 'user_type', 'email',
                  'is_active', 'password1', 'password2', 'username', 'sap_emp_no', 'plant')

    def __init__(self, *args, submit_title=_('save'), **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True

        self.helper.layout = Layout(
            Div(
                Div('user_type', css_class="col-sm-4"),
                Div('emp_no', css_class="col-sm-4"),
                Div(
                    HTML('<div class="form-switch">'),
                    Field('is_active'),
                    HTML('</div>'), css_class='col-md-3 text-center'),
                css_class='row'
            ),
            Div(
                Div('plant', css_class="col-sm-3"),
                Div('username', css_class="col-sm-3"),
                Div('last_name', css_class="col-sm-3"),
                Div('first_name', css_class="col-sm-3"),
                css_class='row'
            ),
            Div(
                Div('email', css_class="col-sm-6"),
                Div('sap_emp_no', css_class="col-sm-3"),
                css_class='row'
            ),
            Div(

                Div('password1', css_class="col-sm-4"),
                Div('password2', css_class="col-sm-4"),
                css_class='row'
            ),
        )

    def clean(self):
        cleaned_data = super(CurrentCustomUserForm, self).clean()
        password = cleaned_data.get("password1")
        confirm_password = cleaned_data.get("password2")

        if password != confirm_password:
            raise forms.ValidationError(
                _('The password is not same with the confirm password')
            )


class UserInfoForm(forms.ModelForm):
    emp_no = forms.CharField(label=_('login_account'), widget=forms.HiddenInput())
    password0 = forms.CharField(label=_('old_password'), required=False,
                                widget=forms.PasswordInput(attrs={'placeholder': _('Please type the login password')}))
    password1 = forms.CharField(label=_('new_password'), required=False,
                                widget=forms.PasswordInput(attrs={'placeholder': _('Please type the new password')}))
    password2 = forms.CharField(label=_('confirm_password'), required=False,
                                widget=forms.PasswordInput(attrs={'placeholder': _('Please type the confirm password')}))
    default_homepage = forms.ModelChoiceField(queryset=HomePageOption.objects.all(), label=_('Default Homepage'),
                                              required=False)

    class Meta:
        model = CustomUser
        fields = ('emp_no', 'email', 'password0', 'password1', 'password2', 'default_homepage')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(UserInfoForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.layout = Layout(
            Fieldset(_('base_information'),
                 Div(
                     Div('emp_no', css_class="col-sm-4"),
                     css_class='row'
                 ),
                 Div(
                     Div('email', css_class="col-sm-4"),
                     css_class='row'
                 ),
            ),
            HTML('<hr>'),
            Fieldset(_('Change Password'),
                Div(
                    Div('password0', css_class="col-sm-4"),
                    css_class='row p-3'
                ),
                Div(
                    Div('password1', css_class="col-sm-4"),
                    Div('password2', css_class="col-sm-4"),
                    css_class='row p-3'
                ),
            ),
            HTML('<hr>'),
        )

    def clean(self):
        cleaned_data = super(UserInfoForm, self).clean()

        emp_no = cleaned_data.get("emp_no")
        current_password = cleaned_data.get("password0")
        password = cleaned_data.get("password1")
        confirm_password = cleaned_data.get("password2")

        if password != confirm_password:
            raise forms.ValidationError(
                _('The password is not same with the confirm password')
            )

        if current_password and not authenticate(username=emp_no, password=current_password):
            raise forms.ValidationError(
                _('The password is not correct')
            )

        return cleaned_data
