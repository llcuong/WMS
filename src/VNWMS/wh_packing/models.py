from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from warehouse.models import Bin, ItemType, MovementType, Warehouse


class Bin_Value(models.Model):
    warehouse = models.ForeignKey(Warehouse, related_name='packing_bin_value_warehouse', on_delete=models.CASCADE)
    bin = models.ForeignKey(Bin, related_name='packing_bin_value_bin', on_delete=models.CASCADE)
    product_order = models.CharField(max_length=50, null=False, blank=False)
    purchase_no = models.CharField(max_length=50, null=True, blank=True)
    version_no = models.CharField(max_length=50, null=True, blank=True)
    version_seq = models.CharField(max_length=50, null=True, blank=True)
    item_type = models.ForeignKey(ItemType, related_name='packing_bin_value_itemtype', on_delete=models.DO_NOTHING)
    size = models.CharField(max_length=5, null=False, blank=False)
    qty = models.IntegerField(blank=True, null=True)
    purchase_unit = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=5, null=False, blank=False)
    stockin_form = models.CharField(max_length=20, blank=True, null=True)
    stockout_form = models.CharField(max_length=20, blank=True, null=True)
    update_at = models.DateTimeField(default=timezone.now)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='packing_bin_value_update_by')


class Bin_Value_History(models.Model):
    warehouse = models.ForeignKey(Warehouse, related_name='packing_bin_value_hist_warehouse', on_delete=models.CASCADE)
    batch_no = models.CharField(max_length=50, null=False, blank=False)
    bin = models.ForeignKey(Bin, related_name='packing_bin_value_hist_bin', on_delete=models.CASCADE)
    product_order = models.CharField(max_length=50, null=False, blank=False)  # PO
    purchase_no = models.CharField(max_length=50, null=True, blank=True)
    version_no = models.CharField(max_length=50, null=True, blank=True)
    version_seq = models.CharField(max_length=50, null=True, blank=True)
    item_type = models.ForeignKey(ItemType, related_name='packing_bin_value_hist_itemtype', on_delete=models.DO_NOTHING)
    size = models.CharField(max_length=5, null=False, blank=False)  # Size
    mvt = models.ForeignKey(MovementType, related_name='packing_bin_value_hist_mvt', on_delete=models.DO_NOTHING)  # Type (STOCKIN / STOCKOUT)
    plus_qty = models.IntegerField()
    minus_qty = models.IntegerField()
    remain_qty = models.IntegerField()
    purchase_unit = models.CharField(max_length=20, blank=True, null=True)
    comment = models.CharField(max_length=200, null=True, blank=True)
    create_at = models.DateTimeField(default=timezone.now)  # Create_at
    create_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name='packing_bin_value_hist_create_by'
    )  # Create_by


class StockInForm(models.Model):
    form_no = models.CharField(max_length=20)
    product_order = models.CharField(max_length=20, blank=True, null=True)
    customer_no = models.CharField(max_length=20, blank=True, null=True)
    version_no = models.CharField(max_length=20, blank=True, null=True)
    version_seq = models.CharField(max_length=20, blank=True, null=True)
    lot_no = models.CharField(max_length=200, blank=True, null=True)
    item_type = models.ForeignKey(ItemType, related_name='packing_stockin_itemtype', on_delete=models.DO_NOTHING)
    purchase_no = models.CharField(max_length=20, blank=True, null=True)
    purchase_qty = models.IntegerField(default=0, blank=True, null=True)
    size = models.CharField(max_length=20, blank=True, null=True)
    purchase_unit = models.CharField(max_length=20, blank=True, null=True)
    post_date = models.CharField(max_length=20, blank=True, null=True)
    order_qty = models.IntegerField(default=0, blank=True, null=True)
    order_bin = models.ForeignKey(Bin, related_name='packing_stockin_order_bin', on_delete=models.DO_NOTHING)
    supplier = models.CharField(max_length=20, blank=True, null=True)
    sap_mtr_no = models.CharField(max_length=20, blank=True, null=True)
    desc = models.CharField(max_length=2000, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, editable=True)  # 建立日期
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='packing_stockin_form_create_by')  # 建立者

    def get_absolute_url(self):
        return reverse('stockin_form', kwargs={'pk': self.pk})


class StockOutForm(models.Model):
    form_no = models.CharField(max_length=20)
    product_order = models.CharField(max_length=20, blank=True, null=True)
    version_no = models.CharField(max_length=20, blank=True, null=True)
    version_seq = models.CharField(max_length=20, blank=True, null=True)
    purchase_no = models.CharField(max_length=20, blank=True, null=True)
    item_type = models.ForeignKey(ItemType, related_name='packing_stockout_itemtype', on_delete=models.DO_NOTHING)
    size = models.CharField(max_length=20, blank=True, null=True)
    purchase_unit = models.CharField(max_length=20, blank=False, null=True)
    order_bin = models.ForeignKey(Bin, related_name='packing_stockout_order_bin', on_delete=models.DO_NOTHING)
    desc = models.CharField(max_length=2000, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, editable=True)  # 建立日期
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='packing_stockout_form_create_by')  # 建立者

    def get_absolute_url(self):
        return reverse('stockout_form', kwargs={'pk': self.pk})


class Series(models.Model):
    key = models.CharField(max_length=50, blank=False, null=False)
    series = models.IntegerField()
    desc = models.CharField(max_length=50, blank=True, null=True)


class SAP_Inventory(models.Model):
    month = models.CharField(max_length=20, null=True)
    warehouse = models.ForeignKey(Warehouse, related_name='packing_sap_inventory_warehouse', on_delete=models.CASCADE)
    product_order = models.CharField(max_length=20, blank=True, null=True)
    customer_no = models.CharField(max_length=20, blank=True, null=True)
    mtr_desc = models.CharField(max_length=200, blank=True, null=True)
    version_no = models.CharField(max_length=20, blank=True, null=True)
    version_seq = models.CharField(max_length=20, blank=True, null=True)
    size = models.CharField(max_length=20, blank=True, null=True)
    qty = models.IntegerField(default=0, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=20, blank=True, null=True)
    post_date = models.DateField(blank=True, null=True)
    location_desc = models.CharField(max_length=20, blank=True, null=True)
    lot_no = models.CharField(max_length=200, blank=True, null=True)
    item_type = models.CharField(max_length=20, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, editable=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='sap_inventory_create_by')


