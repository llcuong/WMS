from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Row, Column, HTML
from django.utils.translation import gettext_lazy as _, get_language
from django import forms

from wh_former.models import Basket_master_data
from wh_former.models import Parameter_data
from wh_former.models import RFID_setting, Former_batch_data, Former_stockout_form

from datetime import date



class BasketMasterDataForm(forms.ModelForm):
    vendor_name = forms.CharField(required=True)
    basket_description = forms.CharField(required=False, label=_('Note'), widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Note')}))
    length_value = forms.CharField(required=True, label=_('Basket width'), widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Length')}))

    class Meta:
        model = Basket_master_data
        fields = ['vendor_name', 'basket_capacity', 'basket_receive_qty', 'basket_receive_date', 'basket_purchase_order']

        labels = {
            'vendor_name': _('Brand'),
            'basket_capacity': _('Capacity'),
            'basket_receive_qty': _('Receive Qty'),
            'basket_receive_date': _('Receive Date'),
            'basket_purchase_order': _('Purchase Order'),
        }

        widgets = {
            'basket_capacity': forms.NumberInput(attrs={'required': True, 'class': 'form-control ', 'min': 1, 'max': 5, 'step': '1', 'placeholder': _('Max: 5'), 'readonly': True}),
            'basket_receive_qty': forms.NumberInput(attrs={'required': True, 'class': 'form-control', 'min': 1, 'step': '1', 'placeholder': _('Example: 24')}),
            'basket_receive_date': forms.DateInput(attrs={'required': True, 'class': 'form-control', 'type': 'date'}),
            'basket_purchase_order': forms.TextInput(attrs={'maxlength': '10', 'minlength': '10', 'required': True, 'class': 'form-control', 'placeholder': _('Type here...')}),
        }

    def clean_basket_receive_qty(self):
        value = self.cleaned_data.get('basket_receive_qty')
        if value is None or value < 1:
            raise forms.ValidationError(_("Why create if you get 0?"))
        return value

    def clean_basket_capacity(self):
        value = self.cleaned_data.get('basket_capacity')
        if value is None or value < 1:
            raise forms.ValidationError(_("A basket without any mold?"))
        return value

    def clean_basket_receive_date(self):
        value = self.cleaned_data.get('basket_receive_date')
        if not value:
            raise forms.ValidationError(_("Please select a receipt date!"))
        return value

    def clean_length_value(self):
        value = self.cleaned_data.get('length_value')
        if not value:
            raise forms.ValidationError(_("Length must be input"))
        return value

    def clean_basket_purchase_order(self):
        value = self.cleaned_data.get('basket_purchase_order')
        if value and len(value) > 10:
            raise forms.ValidationError(_("Product Order cannot exceed 10 characters"))
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['vendor_name'].widget.attrs.update({'class': 'form-control', 'list': 'vendor_name_list'})
        self.vendor_name_list = Parameter_data.objects.filter(group='vendor', belong__contains='basket',
                                                              is_active=True).order_by('code', 'name').values_list('name', flat=True)

        self.fields['basket_receive_date'].widget.attrs['max'] = date.today().strftime('%Y-%m-%d')
        self.fields['basket_receive_date'].initial = date.today()

        self.fields['basket_capacity'].initial = 5

        self.fields['length_value'].widget.attrs.update({'class': 'form-control', 'list': 'params_length_list'})
        self.params_length_list = Parameter_data.objects.filter(group='length', belong__contains='basket',
                                                                is_active=True).order_by('name').values_list('name', flat=True)
        self.fields['basket_purchase_order'].required = True

        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_tag = False




class FormerMasterDataForm(forms.ModelForm):
    class Meta:
        model = Former_batch_data
        fields = ['batch_no', 'former_receive_form', 'former_size',  'former_vendor', 'former_type', 'former_purchase_order',
                  'former_surface', 'former_length', 'former_used_day', 'former_item_no', 'former_aql', 'batch_data_date']
        labels = {
            'former_receive_form': _('DN'),
            'former_size': _('Size'),
            'batch_no': _('Batch No'),
            'former_vendor': _('Brand'),
            'former_type': _('Model'),
            'former_purchase_order': _('Purchase Qty'),
            'batch_data_date': _('Data date'),
            'former_surface': _('Surface'),
            'former_aql': _('AQL'),
            'former_item_no': _('Item No'),
            'former_length': _('Length'),
            'former_used_day': _('Used day'),
        }
        widgets = {
            'former_receive_form': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...'), 'maxlength': '9', 'minlength': '9'}),
            'former_size': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'batch_no': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'former_vendor': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'former_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...')}),
            'former_purchase_order': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...'), 'required': True}),
            'batch_data_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'max': date.today().strftime('%Y-%m-%d'), 'required': True}),
            'former_surface': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...'), 'required': True}),
            'former_aql': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter number...', 'min': '0', 'required': True, 'readonly': True}),
            'former_item_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...'), 'required': True}),
            'former_length': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter number...', 'required': True}),
            'former_used_day': forms.NumberInput(attrs={'class': 'form-control'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['former_size'].widget.attrs.update({'class': 'form-control', 'list': 'params_size_list'})
        self.params_size_list = Parameter_data.objects.filter(group__contains='size', is_active=True).order_by('code').values_list('name', flat=True)

        self.fields['former_vendor'].widget.attrs.update({'class': 'form-control', 'list': 'vendor_name_list'})
        self.vendor_name_list = Parameter_data.objects.filter(group__icontains='vendor', belong__contains='former', is_active=True).order_by('code', 'name').values_list('name', flat=True)

        self.fields['former_item_no'].widget.attrs.update({'class': 'form-control', 'list': 'item_no_list'})
        self.item_no_list = Parameter_data.objects.filter(group__icontains='itemno', is_active=True).order_by('code', 'name').values_list('name', flat=True)

        self.fields['former_length'].widget.attrs.update({'class': 'form-control', 'list': 'params_length_list'})
        self.params_length_list = Parameter_data.objects.filter(group__icontains='length', belong__contains='former', is_active=True).order_by('code', 'name').values_list('name', flat=True)

        self.fields['former_surface'].widget.attrs.update({'class': 'form-control', 'list': 'params_surface_list'})
        # self.params_surface_list = Parameter_data.objects.filter(group__icontains='surface', is_active=True).order_by('code', 'name').values_list('name', flat=True)
        self.params_surface_list = ['Standard Fine Surface', 'Standard Coarse Surface', 'Standard Diamond Textured', 'Energy-saving Fine Surface']

        self.params_type_list = ['Stainless steel', 'Ceramic']


        self.fields['batch_data_date'].initial = date.today()
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_tag = False





class FormerSearchForm(forms.Form):
    former_vendor = forms.CharField(label=_('Brand'), max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    former_type = forms.CharField(label=_('Model'), max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...')}))
    former_surface = forms.CharField(label=_('Surface'), max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...')}))
    former_receive_form = forms.CharField(label=_('Receive Form'), max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...')}))
    former_used_day = forms.CharField(label=_('Used day'), required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '=10, >=10, <=10, >10, <10...'}))
    former_length = forms.FloatField(label=_('Length'), required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter number...'}))
    former_size = forms.CharField(label=_('Size'), required=False, max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    former_item_no = forms.CharField(label=_('Item no'), required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...')}))
    batch_no = forms.CharField(label=_('Batch no'), required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Type here...')}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data:
            data = self.data.copy()
            remap = {
                'vendor_name': 'former_vendor',
                'item_no': 'former_item_no',
                'length_value': 'former_length',
                'params_size': 'former_size',
            }

            for old_name, new_name in remap.items():
                if old_name in data and new_name not in data:
                    data[new_name] = data[old_name]

            self.data = data


        self.fields['former_size'].widget.attrs.update({'class': 'form-control', 'list': 'params_size_list'})
        self.params_size_list = Parameter_data.objects.filter(group__contains='size', is_active=True).values_list('name', flat=True)

        self.fields['former_vendor'].widget.attrs.update({
            'class': 'form-control',
            'list': 'vendor_name_list'
        })
        self.vendor_name_list = Parameter_data.objects.filter(group='vendor', belong__contains='former',
                                          is_active=True).order_by('code', 'name').values_list('name', flat=True)


        self.fields['former_length'].widget.attrs.update({'class': 'form-control', 'list': 'params_length_list'})
        self.params_length_list = Parameter_data.objects.filter(group__icontains='length', belong__contains='former', is_active=True).order_by('code', 'name').values_list('name', flat=True)

        self.fields['former_item_no'].widget.attrs.update({'class': 'form-control', 'list': 'item_no_list'})
        self.item_no_list = Parameter_data.objects.filter(group__icontains='itemno', is_active=True).order_by('code', 'name').values_list('name', flat=True)

        self.params_surface_list = ['Standard Fine Surface', 'Standard Coarse Surface', 'Standard Diamond Textured', 'Energy-saving Fine Surface']

        self.params_type_list = ['Stainless steel', 'Ceramic']

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False

    def clean_used_day(self):
        value = self.cleaned_data.get('former_used_day', '').strip()
        if not value:
            return ''
        import re
        m = re.match(r'^(<=|>=|=|<|>)?\s*(\d+)$', value)
        if m:
            op = m.group(1) or '='
            num = m.group(2)
            return f'{op}{num}'
        raise forms.ValidationError(_('Nhập đúng định dạng: =10, >=10, <=10, >10, <10'))






class BasketSearchForm(forms.Form):
    SEARCH_CHOICES = [('all', _('All')), ('active', _('In use')), ('disable', _('Active')), ('unknown', _('Unknown')), ('scrap', _('Scrap')), ('key', _('Group'))]

    search_filter = forms.ChoiceField(label='', required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    basket_no = forms.CharField(label=_('Basket No'), max_length=128, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter at least 8 characters...')}))
    vendor_name = forms.CharField(label=_('Brand'), max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    basket_receive_date = forms.DateField(label=_('Receive Date'), required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'max': date.today().strftime('%Y-%m-%d')}))
    saved_group = forms.CharField(label=_('Group'), max_length=128, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter group')}))
    purchase_order = forms.CharField(label=_('Purchase Order'), max_length=128, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter PO')}))


    def __init__(self, *args, **kwargs):
        action = kwargs.pop('action', 'search')
        if action == 'search':
            SEARCH_CHOICES = [('all', _('All')), ('disable', _('Active')), ('active', _('In use')), ('unknown', _('Unknown')), ('scrap', _('Scrap'))]
        else:
            SEARCH_CHOICES = [('key', _('Group'))]

        super().__init__(*args, **kwargs)
        self.fields['search_filter'].choices = SEARCH_CHOICES
        self.SEARCH_CHOICES = SEARCH_CHOICES

        self.fields['vendor_name'].widget.attrs.update({
            'class': 'form-control',
            'list': 'vendor_name_list'
        })
        self.vendor_name_list = Parameter_data.objects.filter(group='vendor', belong__contains='basket', is_active=True).order_by('code', 'name').values_list('name', flat=True)
        self.fields['search_filter'].initial = 'all'

        self.params_length_list = Parameter_data.objects.filter(group='length', belong__contains='basket',
                                                                is_active=True).order_by('code', 'name').values_list('name', flat=True)
        self.status_name_list = [label for key, label in self.SEARCH_CHOICES]
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_tag = False






class ManageVendorDataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):

        VALID_GROUPS = ['vendor', 'itemno', 'size', 'length', 'surface']
        group = kwargs.pop('group', 'vendor')
        group = group if group in VALID_GROUPS else 'vendor'
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.instance.group = group

        if group == 'vendor':
            self.fields['name'].label = _('Brand name')
            self.fields.pop('value')
            self.fields.pop('code')
        elif group == 'size':
            self.fields['name'].label = _('Size name')
            self.fields.pop('code')
            self.fields.pop('value')
        elif group == 'itemno':
            self.fields['name'].label = _('Item name')
            self.fields.pop('code')
            self.fields['value'].widget = forms.HiddenInput()
            if not self.instance.pk:
                self.fields['value'].initial = 1
        elif group == 'length':
            self.fields['code'].label = _('Length code')
            self.fields['name'].label = _('Length')
            self.fields.pop('value')
        elif group == 'surface':
            self.fields['name'].label = _('Surface')
            self.fields.pop('code')
            self.fields.pop('value')


        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False

        if group == 'vendor':
            self.helper.layout = Layout(
                Row(
                    Column('name', css_class='col-md-4 mb-0'),
                )
            )
        elif group == 'size':
            self.helper.layout = Layout(
                Row(
                    Column('name', css_class='col-md-4 mb-0'),
                )
            )
        elif group == 'length':
            self.helper.layout = Layout(
                Row(
                    Column('name', css_class='col-md-4 mb-0'),
                )
            )
        elif group == 'surface':
            self.helper.layout = Layout(
                Row(
                    Column('name', css_class='col-md-4 mb-0'),
                )
            )
        else:
            self.helper.layout = Layout(
                Row(
                    Column('name', css_class='col-md-4 mb-0'),
                )
            )

    def clean_value(self):
        raw = self.data.get(self.add_prefix('value'), '').replace(',', '.').strip()
        try:
            value = float(raw)
        except ValueError:
            raise forms.ValidationError(_("Giá trị không hợp lệ."))
        if value < 0:
            raise forms.ValidationError(_("Giá trị không được nhỏ hơn 0."))
        return value

    class Meta:
        model = Parameter_data
        fields = ['code', 'name', 'value']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        }





class ManageSettingForm(forms.ModelForm):
    class Meta:
        model = RFID_setting
        fields = ['client_device_ip', 'rfid_reader_ip', 'rfid_reader_port', 'location_name', 'rfid_reader_status']
        labels = {
            'client_device_ip': _('Client Device IP'),
            'rfid_reader_ip': _('RFID Reader IP'),
            'rfid_reader_port': _('RFID Reader Port'),
            'location_name': _('Location Name'),
            'rfid_reader_status': _('RFID Reader Status'),
        }
        widgets = {
            'client_device_ip': forms.TextInput(attrs={'class': 'form-control'}),
            'rfid_reader_ip': forms.TextInput(attrs={'class': 'form-control'}),
            'rfid_reader_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'location_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rfid_reader_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Div('client_device_ip', css_class='col-md-3'),
                Div('rfid_reader_ip', css_class='col-md-3'),
                Div('rfid_reader_port', css_class='col-md-3'),
                Div('location_name', css_class='col-md-3'),
                css_class='row mb-3'
            ),
            Div(
                Div('rfid_reader_status', css_class='col-md-3'),
                css_class='row mb-3'
            ),
            Div(
                Div(
                    Submit('submit', _('Save'), css_class='btn btn-primary'),
                    HTML('&nbsp;&nbsp;&nbsp;'),
                    HTML(
                        '<buttons type="buttons" class="btn btn-danger ms-2" onclick="window.location.href=\'{% url "manage_wh_former_index" %}\'">Close</buttons>'),
                    css_class='d-flex justify-content-center gap-2'
                ),
                css_class='text-center mt-3'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        # self._duplicate = False
        # rfid_ip = cleaned_data.get('rfid_reader_ip')
        # port = cleaned_data.get('rfid_reader_port')
        # if rfid_ip and port:
        #     qs = RFID_setting.objects.filter(
        #         rfid_reader_ip=rfid_ip,
        #         rfid_reader_port=port
        #     )
        #     if self.instance.pk:
        #         qs = qs.exclude(pk=self.instance.pk)
        #
        #     if qs.exists():
        #         self._duplicate = True
        #         raise forms.ValidationError(_("RFID Reader IP and Port combination must be unique."))
        return cleaned_data


class StockDataRecordForm(forms.ModelForm):
    size = forms.CharField(
        label=_('Size:'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Select size')})
    )

    class Meta:
        model = Former_stockout_form
        fields = ['stockout_form']
        labels = {
            'stockout_form': _('Stock form'),
        }
        widgets = {
            'stockout_form': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),  # Sửa từ 'stock_form' thành 'stockout_form'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sizes = list(Parameter_data.objects.filter(group__contains='size', is_active=True).values_list('name', flat=True))
        self.params_size_list = sizes

        self.fields['size'].widget.attrs.update({
            'class': 'form-control',
            'list': 'params_size_list',
        })
        self.fields['stockout_form'].required = True

        if sizes:
            self.fields['size'].initial = sizes[0]

    def clean_size(self):
        size = self.cleaned_data.get('size')
        if size not in self.params_size_list:
            raise forms.ValidationError(_("Invalid size selected. Please choose a valid size."))
        return size





