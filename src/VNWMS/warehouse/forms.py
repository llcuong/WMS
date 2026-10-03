from warehouse.models import Warehouse, Area, Bin, Plant
from django.utils.translation import gettext_lazy as _
from django import forms


class WarehouseForm(forms.ModelForm):
    wh_plant = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Warehouse
        fields = [
            'wh_code',
            'wh_name',
            'wh_comment',
            'wh_plant',
            'wh_bg',
            'wh_packing_func',
            'wh_former_func',
            'wh_wip_func',
            'wh_product_func',
        ]

    wh_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    wh_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    wh_comment = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))
    wh_packing_func = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input big-checkbox'}
        )
    )
    wh_former_func = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input big-checkbox'}
        )
    )
    wh_wip_func = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input big-checkbox'}
        )
    )
    wh_product_func = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input big-checkbox'}
        )
    )

    wh_bg = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    def save(self, commit=True):
        # Lấy instance của Warehouse từ dữ liệu form
        instance = super().save(commit=False)

        # Thực hiện các xử lý bổ sung trước khi lưu (nếu cần)
        if commit:
            instance.save()
        return instance

    def edit(self, commit=True):
        # Lấy instance của Warehouse từ dữ liệu form
        instance = super().save(commit=False)

        # Thực hiện các xử lý bổ sung trước khi lưu (nếu cần)
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lấy danh sách Plant từ database
        plant_choices = Plant.objects.values_list('plant_code', 'plant_name')

        # Gán danh sách lựa chọn vào ChoiceField
        self.fields['wh_plant'].choices = [('', _('Choose Plant'))] + list(plant_choices)

        # Kiểm tra nếu là form chỉnh sửa
        if self.instance and self.instance.pk:  # Kiểm tra nếu đối tượng đã tồn tại
            self.fields['wh_code'].widget.attrs['readonly'] = 'readonly'


class AreaForm(forms.ModelForm):
    LAYER_CHOICES = [
        (None, "------"),
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6)
    ]

    class Meta:
        model = Area
        fields = ['area_id', 'area_name', 'pos_x', 'pos_y', 'area_w', 'area_l', 'warehouse', 'layer']

    area_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    area_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pos_x = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    pos_y = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    area_w = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    area_l = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),  # Lấy tất cả các đối tượng Warehouse
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    layer = forms.ChoiceField(
        choices=LAYER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(self.fields['warehouse'].queryset)  # Debug queryset
        # Kiểm tra nếu là form chỉnh sửa
        if self.instance and self.instance.pk:  # Kiểm tra nếu đối tượng đã tồn tại
            self.fields['area_id'].widget.attrs['readonly'] = 'readonly'

    def save(self, commit=True):
        # Lấy instance của Warehouse từ dữ liệu form
        instance = super().save(commit=False)

        # Thực hiện các xử lý bổ sung trước khi lưu (nếu cần)
        if commit:
            instance.save()
        return instance

    def edit(self, commit=True):
        # Lấy instance của Warehouse từ dữ liệu form
        instance = super().save(commit=False)

        # Thực hiện các xử lý bổ sung trước khi lưu (nếu cần)
        if commit:
            instance.save()
        return instance


class BinForm(forms.ModelForm):
    class Meta:
        model = Bin
        fields = ['bin_id', 'bin_name', 'area']

    bin_id = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bin_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),  # Lấy tất cả các đối tượng Area
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def save(self, commit=True):
        # Lấy instance của Bin từ dữ liệu form
        instance = super().save(commit=False)

        # Thực hiện các xử lý bổ sung trước khi lưu (nếu cần)
        if commit:
            instance.save()
        return instance

    def edit(self, commit=True):
        # Lấy instance của Warehouse từ dữ liệu form
        instance = super().save(commit=False)

        # Thực hiện các xử lý bổ sung trước khi lưu (nếu cần)
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kiểm tra nếu là form chỉnh sửa
        if self.instance and self.instance.pk:  # Kiểm tra nếu đối tượng đã tồn tại
            self.fields['bin_id'].widget.attrs['readonly'] = 'readonly'

