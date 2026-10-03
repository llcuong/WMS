from datetime import timedelta, date, datetime
from crispy_forms.bootstrap import AppendedText
from bootstrap_datepicker_plus.widgets import DatePickerInput
from django.http import request
from django_select2.forms import Select2Widget

from warehouse.models import Warehouse, Bin, ItemType, UnitType, Area, Plant
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Row, Column
from django.utils.translation import gettext_lazy as _, get_language
from django import forms


class BinValueForm(forms.Form):
    bin = forms.CharField(
        required=True,
        label=_('Bin'),
        max_length=20,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )
    po_no = forms.CharField(required=True, label=_('Product Order'), max_length=20)
    size = forms.CharField(required=True, label=_('Size'), max_length=20)
    qty = forms.IntegerField(required=True, label=_('Qty'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.layout = Layout(
            Div(
                Div('bin', css_class='col-md-10'),
                Div(
                    HTML(
                        f"<div id='history_link'></div>"),
                    css_class='col-md-2'
                ),
                css_class='row'
            ),
            Div(
                Div('po_no', css_class='col-md-12'),
                css_class='row'
            ),
            Div(
                Div('size', css_class='col-md-12'),
                css_class='row'
            ),
            Div(
                Div('qty', css_class='col-md-12'),
                css_class='row'
            ),
        )


class CustomModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_item_type_name()  # Sử dụng phương thức get_item_type_name để hiển thị tên


class BinSearchForm(forms.Form):
    plant = forms.ChoiceField(
        required=True,
        label=_("Plant"),
        choices=[('', '---------')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    bin = forms.ChoiceField(
        required=False,
        label=_("Location:"),
        choices=[],
        widget=Select2Widget(attrs={'class': 'form-control'}),
    )
    po_no = forms.CharField(
        required=False,
        label=_("Product Order"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    pu_no = forms.CharField(
        required=False,
        label=_("purchase_order"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    size = forms.CharField(
        required=False,
        label=_("Size"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    lot = forms.CharField(
        required=False,
        label=_("Lot"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        disabled=True
    )
    item_type = CustomModelChoiceField(
        queryset=ItemType.objects.all(),
        # empty_label="-- Choice Items --"
        required=False,
        label=_("Item Type"),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    version_no = forms.CharField(
        required=False,
        label=_("Version No"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    from_date = forms.DateField(
        required=False,
        label=_("From"),
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d'
        )
    )
    to_date = forms.DateField(
        required=False,
        label=_("To"),
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d'
        )
    )

    def __init__(self, *args, **kwargs):
        day7_ago = date.today() - timedelta(days=7)
        today = date.today()
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            qs = Bin.objects.filter(
                area__warehouse__wh_packing_func=True,
                # area__warehouse__wh_plant=user.plant
            ).values('bin_id', 'bin_name')

            self.fields['bin'].choices = [(b['bin_id'], b['bin_name']) for b in qs]
        self.fields['plant'].choices = [(p['plant_code'], p['plant_name']) for p in Plant.objects.values('plant_code', 'plant_name')]
        self.fields['plant'].initial = user.plant
        self.fields['from_date'].initial = day7_ago
        self.fields['to_date'].initial = today


class BinTransferForm(forms.Form):
    bin = forms.ModelChoiceField(
        queryset=Bin.objects.none(),
        label=_("Location:"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control select2-bin'})
    )

    qty = forms.IntegerField(
        label=_("Quantity"),
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['bin'].queryset = Bin.objects.filter(
            area__warehouse__wh_packing_func=True,
            area__warehouse__wh_plant=user.plant
        ).order_by('bin_id')

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.layout = Layout(
            Div(
                Div('bin', css_class='m-1'),
                Div('qty', css_class='m-1'),
                Div(Submit('submit', _('Confirm'), css_class='btn btn-primary m-1')),
                css_class='form-inline d-flex justify-content-end'
            ),
        )


class QuantityAdjustForm(forms.Form):

    qty = forms.IntegerField(label=_("New Quantity"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.layout = Layout(
            Div(
                Div('qty', css_class='m-1'),
                Div(Submit('submit', _('Confirm'), css_class='btn btn-primary m-1')),
                css_class='form-inline d-flex justify-content-end mt-3'
            ),
        )


class StockInPForm(forms.Form):
    product_order = forms.CharField(max_length=20, label=_("Product Order"), required=True, )  # VBELN 收貨單號
    customer_no = forms.CharField(max_length=20, label=_("Customer"), required=False,)  # 無
    version_no = forms.CharField(max_length=20, label=_("Version No"), required=True,)  # ZZVERSION
    version_seq = forms.CharField(max_length=20, label=_("Version Sequence"), required=False, )  # ZZVERSION_SEQ
    lot_no = forms.CharField(max_length=20, label=_("Lot Number"), required=False, )  # LOTNO
    item_type = forms.ModelChoiceField(queryset=ItemType.objects.all(), label=_("Item Type"), required=True)
    purchase_no = forms.CharField(max_length=20, label=_("Purchase Order"), required=True, )  # EBELN 採購單號
    purchase_qty = forms.CharField(
        max_length=20,
        label=_("Purchase Quantity"),
        required=False,
        initial=0,
        widget=forms.TextInput(attrs={'class': 'text-right'})

    )  # MENGE_PO 採購數量
    size = forms.CharField(max_length=20, label=_("Size"), required=False, )
    purchase_unit = forms.ModelChoiceField(queryset=UnitType.objects.all(), label=_("Unit"), required=False)
    post_date = forms.DateField(label=_("Post Date"), required=True)  # BUDAT收貨日期
    order_qty = forms.CharField(
        max_length=20,
        label=_("Quantity"),
        required=False,
        initial=0,
        widget=forms.TextInput(attrs={'class': 'text-right'})
    )  # MENGE

    order_bin = forms.ModelChoiceField(
        queryset=Bin.objects.none(),
        label=_("Location:"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2-bin'})
    )
    supplier = forms.CharField(max_length=10, label=_("Supplier"), required=False)  # NAME1
    sap_mtr_no = forms.CharField(max_length=20, label=_("SAP Material Number"), required=False, )  # MBLNR
    desc = forms.CharField(max_length=2000, label=_("Comment"), required=False, widget=forms.Textarea(attrs={'rows': 2, 'cols': 15}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        if user:  # nếu có user thì filter queryset
            self.fields['order_bin'].queryset = Bin.objects.filter(
                area__warehouse__wh_packing_func=True,
                area__warehouse__wh_plant=user.plant
            ).order_by('bin_id')

        # 📌 Lấy ngôn ngữ hiện tại
        lang = get_language()

        # 📌 Tuỳ chỉnh `queryset` của `item_type`
        if lang == 'vi':
            self.fields['item_type'].queryset = ItemType.objects.filter(type_vn_name__isnull=False)\
                .order_by('type_vn_name')
            self.fields['item_type'].label_from_instance = lambda obj: obj.type_vn_name
        elif lang == 'zh-hant':
            self.fields['item_type'].queryset = ItemType.objects.filter(type_name__isnull=False).order_by('type_name')
            self.fields['item_type'].label_from_instance = lambda obj: obj.type_name
        else:
            self.fields['item_type'].queryset = ItemType.objects.filter(type_code__isnull=False).order_by('type_code')
            self.fields['item_type'].label_from_instance = lambda obj: obj.type_code

        # 📌 Cấu hình Crispy Forms
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True

        self.helper.layout = Layout(
            Div(
                # Div('purchase_no', css_class='col-md-3'),
                Div(AppendedText(
                    'purchase_no',
                    '<button type="button" id="_purchase_no" class="btn btn-sm btn-outline-secondary p-0" '
                    'style="height: 24px; width: 25px; display: flex; '
                    'align-items: center; justify-content: center;" aria-label="Purchase Order">'
                    '<i class="fas fa-search"></i>'
                    '</button>'
                ), css_class='col-md-3'),
                Div('customer_no', css_class='col-md-3'),
                Div('version_no', css_class='col-md-3'),
                Div('version_seq', css_class='col-md-3'),
                css_class='row'),
            Div(
                # Div('product_order', css_class='col-md-3'),
                Div(AppendedText(
                    'product_order',
                    '<button type="button" id="_product_order" class="btn btn-sm btn-outline-secondary p-0" '
                    'style="height: 24px; width: 25px; '
                    'display: flex; align-items: center; justify-content: center;" aria-label="Product Order">'
                    '<i class="fas fa-search"></i>'
                    '</button>'
                ), css_class='col-md-3'),
                Div('sap_mtr_no', css_class='col-md-3'),
                Div('item_type', css_class='col-md-3'),
                css_class='row'),
            Div(
                Div('post_date', css_class='col-md-3'),
                Div('supplier', css_class='col-md-3'),
                Div('lot_no', css_class='col-md-3'),
                Div('size', css_class='col-12 col-md-3'),
                Div('purchase_qty', css_class='col-md-3'),
                Div('purchase_unit', css_class='col-md-3'),
                Div('order_qty', css_class='col-md-3'),
                Div('order_bin', css_class='col-md-3'),
                Div('desc', css_class='col-md-10'),
                Div(HTML(
                    '<a href="#" class="btn btn-info" id="create""><i class="fas fa-plus-circle"></i> '+_('Add')+'</a>'),
                    css_class='col-md-2 d-flex align-items-center pt-3'),
                css_class='row'),
        )

        self.fields['post_date'].widget = DatePickerInput(
            attrs={'value': (datetime.now()).strftime('%Y-%m-%d')},
            options={
                "format": "YYYY-MM-DD",
                "showClose": False,
                "showClear": False,
                "showTodayButton": False,
            }
        )


class StockOutPForm(forms.Form):
    product_order = forms.CharField(max_length=20, label=_("Product Order"), required=False, )  # VBELN 收貨單號
    purchase_no = forms.CharField(max_length=20, label=_("Purchase Order"), required=False, )  # EBELN 採購單號

    size = forms.CharField(max_length=20, label=_("Size"), required=False, )
    lot_no = forms.CharField(max_length=20, label=_("Lot Number"), required=False, )
    version_no = forms.CharField(max_length=20, label=_("Version No"), required=False, )
    item_type = forms.ModelChoiceField(queryset=ItemType.objects.all(), label=_("Item Type"), required=False, )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 📌 Lấy ngôn ngữ hiện tại
        lang = get_language()

        # 📌 Tuỳ chỉnh `queryset` của `item_type`
        if lang == 'vi':
            self.fields['item_type'].queryset = ItemType.objects.filter(type_vn_name__isnull=False) \
                .order_by('type_vn_name')
            self.fields['item_type'].label_from_instance = lambda obj: obj.type_vn_name
        elif lang == 'zh-hant':
            self.fields['item_type'].queryset = ItemType.objects.filter(type_name__isnull=False).order_by('type_name')
            self.fields['item_type'].label_from_instance = lambda obj: obj.type_name
        else:
            self.fields['item_type'].queryset = ItemType.objects.filter(type_code__isnull=False).order_by('type_code')
            self.fields['item_type'].label_from_instance = lambda obj: obj.type_code

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True

        self.helper.layout = Layout(
            Div(
                Div('product_order', css_class='col-md-4'),
                Div('purchase_no', css_class='col-md-4'),
                Div('size', css_class='col-md-4'),
                css_class='row mb-3'
            ),
            Div(
                Div('lot_no', css_class='col-md-4'),
                Div('version_no', css_class='col-md-4'),
                Div('item_type', css_class='col-md-4'),
                css_class='row mb-3'
            ),
        )


class ExcelUploadForm(forms.Form):
    file = forms.FileField(
        label=_("Choose Excel File"),
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False


class Excel2UploadForm(forms.Form):

    file_type = forms.ChoiceField(
        label=_("Select Type"),
        widget=forms.Select(attrs={"class": "form-control"})
    )
    file = forms.FileField(
        label=_("Choose Excel File"),
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = [('', '------')]
        choices += [(wh['wh_code'], wh['wh_name'])for wh in Warehouse.objects.filter(wh_code__icontains='PKG').values('wh_code', 'wh_name')]
        self.fields['file_type'].choices = choices

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.layout = Layout(
            Row(
                Column('file_type', css_class='form-group col-md-4 mb-0'),
                Column('file', css_class='form-group col-md-6 mb-0'),
                Column(
                    HTML("""
                            <a href="{% url 'download_excel_template' 'stock_data_import.xlsx' %}" class="btn btn-info w-100" aria-label="template">
                                <i class="fas fa-download"></i>
                            </a>
                        """),
                    css_class='form-grouptext-center'
                ),
                css_class='form-row align-items-end'
            ),
            Column(Submit('submit', 'Upload'), css_class='form-group'),

        )


class SAPUploadForm(forms.Form):

    plant = forms.ChoiceField(
        required=True,
        label=_("Plant"),
        widget=forms.Select(attrs={"class": "form-control"})
    )
    month = forms.CharField(
        widget=forms.DateInput(attrs={
            'type': 'month'
        }),
        label=_("Choose Month")
    )
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
        label=_("Choose Excel File")

    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = [('', '------')]
        choices += [(wh['wh_code'], wh['wh_name']) for wh in Warehouse.objects.filter(wh_code__icontains='PKG').values('wh_code', 'wh_name')]
        self.fields['plant'].choices = choices

        self.helper = FormHelper()
        self.helper.form_tag = False


class SAPQueryForm(forms.Form):
    plant = forms.ChoiceField(
        required=True,
        choices=[
            ('', '---'),
            ('GDNBR', 'NBR'),
            ('GDPVC', 'PVC')
        ],
        label=_("Plant"),
        widget=forms.Select(attrs={"class": "form-control"})
    )
    month = forms.CharField(
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'm-1'
        }),
        label=_("Choose Month")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False


class BinValueSearchForm(forms.Form):
    warehouse = forms.ChoiceField(
        choices=[], required=False, widget=forms.Select(attrs={"class": "form-control"})
    )
    area = forms.ChoiceField(
        choices=[], required=False, widget=forms.Select(attrs={"class": "form-control", "disabled": "disabled"})
    )
    bin = forms.ChoiceField(
        choices=[], required=False, widget=forms.Select(attrs={"class": "form-control", "disabled": "disabled"})
    )
    po = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["warehouse"].choices = [("", _("Choose Warehouse"))] + list(Warehouse.objects.values_list("wh_code",
                                                                                                           "wh_name"))
        self.fields["area"].choices = [("", _("Choose Area"))]
        self.fields["bin"].choices = [("", _("Choose Location"))]


class BinValueDeleteForm(forms.Form):
    warehouse = forms.ChoiceField(
        choices=[], required=False, widget=forms.Select(attrs={"class": "form-control"})
    )
    area = forms.ChoiceField(
        choices=[], required=False, widget=forms.Select(attrs={"class": "form-control", "disabled": "disabled"})
    )
    bin = forms.ChoiceField(
        choices=[], required=False, widget=forms.Select(attrs={"class": "form-control", "disabled": "disabled"})
    )

    po = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse"].choices = [("", _("Choose Warehouse"))] + list(Warehouse.objects.values_list("wh_code",
                                                                                                           "wh_name"))
        self.fields["area"].choices = [("", _("Choose Area"))]
        self.fields["bin"].choices = [("", _("Choose Location"))]


class BatchSearchForm(forms.Form):
    batch = forms.CharField(required=False, label=_("Batch No"))
