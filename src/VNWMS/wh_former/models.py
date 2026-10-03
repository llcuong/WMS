from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator

from warehouse.models import Area, Bin





class Basket_master_data(models.Model):
    basket_no = models.CharField(max_length=20, null=False, primary_key=True)
    basket_vendor = models.CharField(max_length=50, null=True, blank=True)
    basket_capacity = models.IntegerField(blank=False, null=False)
    basket_length = models.CharField(max_length=50, null=True, blank=True)
    basket_receive_qty = models.IntegerField(null=False, blank=False)
    basket_receive_date = models.DateField(null=False, blank=False)
    basket_purchase_order = models.CharField(max_length=10, null=True, blank=True, validators=[MinLengthValidator(10)])
    former_size = models.CharField(max_length=10, null=True, blank=True)
    former_used_day = models.IntegerField(default=0, null=False)
    is_active = models.IntegerField(default=0, null=False)
    is_print = models.IntegerField(default=0, blank=False, null=False)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='basket_master_data_create_by')
    create_at = models.DateTimeField(auto_now_add=True)



class Basket_master_data_log(models.Model):
    basket_no = models.ForeignKey(Basket_master_data, to_field='basket_no', db_column='basket_no', primary_key=True, on_delete=models.CASCADE, related_name='basket_master_data_log_key')
    basket_series = models.IntegerField(blank=False, null=False)
    saved = models.CharField(max_length=15, blank=True, null=True)
    basket_description = models.CharField(max_length=200, null=True, blank=True)
    basket_stockin_date = models.CharField(max_length=40, null=True, blank=True)



class Basket_master_data_print_log(models.Model):
    basket_purchase_order = models.CharField(max_length=10, null=False, blank=False)
    basket_vendor = models.CharField(max_length=50, null=False, blank=False)
    basket_receive_date = models.DateField(null=False, blank=False)
    plant_code = models.CharField(max_length=5, null=False, blank=False)
    basket_receive_qty = models.IntegerField(null=False, blank=False)
    basket_printed_qty = models.IntegerField(null=False, blank=False)
    basket_created_qty = models.IntegerField(null=False, blank=False)
    basket_length = models.CharField(max_length=50, null=True, blank=True)
    saved = models.CharField(max_length=15, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)




class Former_batch_data(models.Model):
    group_batch = models.CharField(max_length=25, blank=True, null=True)
    batch_no = models.CharField(max_length=25, unique=True, blank=False, null=False)
    former_receive_form = models.CharField(max_length=9, null=True, blank=True)
    former_size = models.CharField(max_length=5, null=True, blank=True)
    former_vendor = models.CharField(max_length=50, null=True, blank=True)
    former_type = models.CharField(max_length=50, null=True, blank=True)
    former_purchase_order = models.CharField(max_length=50, null=True, blank=True)
    former_surface = models.CharField(max_length=50, null=True, blank=True)
    former_length = models.FloatField(null=True, blank=True)
    former_used_day = models.IntegerField(default=0, blank=False, null=False)
    former_item_no = models.CharField(max_length=100, null=True, blank=True)
    former_aql = models.FloatField(default=1.0, blank=False, null=False)
    is_active = models.BooleanField(default=True)
    batch_data_date = models.DateField(null=False, blank=True)
    batch_last_stockout = models.DateField(null=True, blank=True)
    batch_total_basket = models.IntegerField(default=0, blank=True, null=True)
    batch_total_basket_in_wh = models.IntegerField(default=0, blank=True, null=True)
    batch_total_former = models.IntegerField(default=0, blank=True, null=True)
    batch_total_former_in_wh = models.IntegerField(default=0, blank=True, null=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='former_batch_data_create_by')
    create_at = models.DateTimeField(auto_now_add=True)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='former_batch_data_update_by')
    update_at = models.DateTimeField(auto_now=True)



class Former_batch_data_log(models.Model):
    batch_no = models.CharField(max_length=25, blank=False, null=False)
    batch_combine = models.CharField(max_length=25, blank=True, null=True)
    batch_action_name = models.CharField(max_length=25, blank=False, null=False)
    batch_stockout_to = models.CharField(max_length=25, blank=True, null=True)

    batch_qty_stockout = models.IntegerField(default=0, blank=False, null=False)
    batch_qty_stockin = models.IntegerField(default=0, blank=False, null=False)
    batch_qty_merge = models.IntegerField(default=0, blank=False, null=False)
    batch_qty_split = models.IntegerField(default=0, blank=False, null=False)
    batch_qty_in_wh = models.IntegerField(default=0, blank=False, null=False)
    batch_qty_total = models.IntegerField(default=0, blank=False, null=False)

    batch_used_day = models.IntegerField(default=0, blank=True, null=True)
    batch_sub_action_name = models.CharField(max_length=25, blank=True, null=True)
    batch_sub_action_key = models.CharField(max_length=25, blank=True, null=True)
    batch_change_day = models.DateField(auto_now=True)

    batch_basket_qty_stockout = models.IntegerField(default=0, blank=False, null=False)
    batch_basket_qty_stockin = models.IntegerField(default=0, blank=False, null=False)
    batch_basket_qty_merge = models.IntegerField(default=0, blank=False, null=False)
    batch_basket_qty_split = models.IntegerField(default=0, blank=False, null=False)
    batch_basket_qty_in_wh = models.IntegerField(default=0, blank=False, null=False)
    batch_basket_qty_total = models.IntegerField(default=0, blank=False, null=False)

    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_confirmed = models.BooleanField(default=False, blank=True, null=True)

    # rfid_reader_ip = models.CharField(max_length=15, null=False, blank=False)
    # create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='former_batch_log_data_create_by')



class Former_master_data_scan_log(models.Model):
    batch_dn = models.CharField(max_length=9, null=True, blank=True)
    batch_item_no = models.CharField(max_length=100, null=True, blank=True)
    batch_used_day = models.IntegerField(default=0, blank=True, null=True)
    batch_purchase_order = models.CharField(max_length=50, null=True, blank=True)
    batch_data_date = models.DateField(null=False, blank=True)
    batch_former_vendor = models.CharField(max_length=50, null=True, blank=True)
    batch_former_type = models.CharField(max_length=50, null=True, blank=True)
    batch_former_surface = models.CharField(max_length=50, null=True, blank=True)
    batch_former_size = models.CharField(max_length=5, null=True, blank=True)
    batch_former_length = models.FloatField(null=True, blank=True)
    batch_former_aql = models.FloatField(default=1.0, blank=False, null=False)
    batch_no = models.CharField(max_length=25, unique=True, blank=False, null=False)
    batch_purchase_received = models.IntegerField(blank=True, null=True)




#
#
# class Former_batch_rack(models.Model):
#     batch_no = models.ForeignKey(Former_batch_data, to_field='batch_no', db_column='batch_no', on_delete=models.CASCADE)
#     rack_no = models.CharField(max_length=10, null=True, blank=True)
#     bin = models.CharField(max_length=10, null=True, blank=True)
#
#
#
# class Former_rack_bin(models.Model):
#     rack_no = models.CharField(max_length=10, null=True, blank=True)
#     basket_no = models.ForeignKey(Basket_master_data, to_field='basket_no', db_column='basket_no', on_delete=models.CASCADE, unique=True)
#     basket_former_qty = models.IntegerField(blank=False, null=False, default=0)
#
#
#



class Former_bin_data(models.Model):
    batch_no = models.ForeignKey(Former_batch_data, to_field='batch_no', db_column='batch_no', on_delete=models.CASCADE)
    basket_no = models.ForeignKey(Basket_master_data, to_field='basket_no', db_column='basket_no', on_delete=models.CASCADE, unique=True)
    bin = models.CharField(max_length=10, null=True, blank=True)
    basket_former_qty = models.IntegerField(blank=False, null=False, default=0)
    to_bin_key = models.CharField(max_length=30, null=True, blank=True)
    update_at = models.DateTimeField(auto_now=True, blank=True)


class Former_bin_data_log(models.Model):
    batch_no = models.ForeignKey(Former_batch_data, to_field='batch_no', db_column='batch_no', on_delete=models.CASCADE)
    basket_no = models.ForeignKey(Basket_master_data, to_field='basket_no', db_column='basket_no', on_delete=models.CASCADE)
    from_bin = models.CharField(max_length=30, null=True, blank=True)
    to_bin = models.CharField(max_length=30, null=True, blank=True)
    basket_former_qty = models.IntegerField(blank=False, null=False)
    action = models.CharField(max_length=30, null=True, blank=True)
    action_form = models.CharField(max_length=30, null=True, blank=True)
    former_size = models.CharField(max_length=5, null=True, blank=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='former_basket_bin_create_by')
    create_at = models.DateTimeField(auto_now_add=True)




class Former_rack_bin_temp(models.Model):
    client_device_ip = models.CharField(max_length=15, null=True, blank=True)
    rfid_reader_ip = models.CharField(max_length=15, null=True, blank=True)
    pid = models.IntegerField(null=False)
    batch_no = models.CharField(max_length=25, blank=True, null=True)
    action = models.CharField(max_length=30, null=True, blank=True)
    rack_temp_id = models.CharField(max_length=50, null=True, blank=True)
    rack_scan_order = models.IntegerField(default=1, blank=True, null=True)
    rack_total_basket = models.IntegerField(default=0, blank=True, null=True)
    rack_total_former = models.IntegerField(default=0, blank=True, null=True)
    from_bin = models.CharField(max_length=30, null=True, blank=True)
    to_bin = models.CharField(max_length=30, null=True, blank=True)
    stock_form = models.CharField(max_length=30, null=True, blank=True)



class Former_rack_basket_temp(models.Model):
    rack_temp_id = models.CharField(max_length=50, null=False, blank=False)
    basket_no = models.CharField(max_length=20, null=False, unique=True)
    basket_former_qty = models.IntegerField(blank=False, null=False)
    batch_no = models.CharField(max_length=25, blank=True, null=True)



class Former_stockout_form(models.Model):
    stockout_form = models.CharField(max_length=30, null=True, blank=True)
    stockout_date = models.DateField(auto_now_add=True)
    stockout_action = models.CharField(max_length=20, null=True, blank=True)
    stockout_to = models.CharField(max_length=20, null=True, blank=True)
    stockout_from = models.CharField(max_length=5, null=True, blank=True)
    batch_no = models.CharField(max_length=25, blank=True, null=True)
    former_size = models.CharField(max_length=5, null=True, blank=True)
    stockout_total_basket = models.IntegerField(default=0, null=False)
    stockout_total_former = models.IntegerField(default=0, null=False)
    stockout_return_basket = models.IntegerField(default=0, null=False)
    stockout_return_former = models.IntegerField(default=0, null=False)
    machine_workorder = models.CharField(max_length=20, null=True, blank=True)
    most_batch_former_qty = models.IntegerField(default=0, null=False)
    most_batch_used_day = models.IntegerField(default=0, null=False)
    is_closed = models.BooleanField(default=False)
    stockin_date = models.DateField(null=True, blank=True)
    is_confirmed = models.BooleanField(default=False, blank=True, null=True)


class RFID_setting(models.Model):
    client_device_ip = models.CharField(max_length=15, null=False, blank=False)
    rfid_reader_ip = models.CharField(max_length=15, null=False, blank=False)
    rfid_reader_port = models.IntegerField(blank=False, null=False)
    location_name = models.CharField(max_length=15, null=False, blank=False)
    rfid_reader_status = models.BooleanField(default=True)
    rfid_reader_state = models.BooleanField(default=False)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='rfid_setting_create_by')
    create_at = models.DateTimeField(auto_now_add=True, editable=True)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='rfid_setting_update_by')
    update_at = models.DateTimeField(default=timezone.now)
    is_control = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.rfid_reader_status:
            self.rfid_reader_state = False
        super().save(*args, **kwargs)




class Parameter_data(models.Model):
    group = models.CharField(max_length=50, null=False, blank=False)
    code = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    value = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    belong = models.CharField(max_length=50, null=True, blank=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='parameter_data_create_by')
    create_at = models.DateTimeField(auto_now_add=True, editable=True)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='parameter_data_update_by')
    update_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('group', 'belong', 'name')



class RFID_read(models.Model):
    basket_no = models.CharField(max_length=50, null=False)
    rfid_reader_ip = models.CharField(max_length=15, null=False, blank=False)
    pid = models.IntegerField(null=True, blank=True)
    is_saved = models.BooleanField(default=False)
    is_passed = models.BooleanField(default=False)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='rfid_read_create_by')
    create_at = models.DateTimeField(auto_now_add=True, editable=True)


class RFID_read_log(models.Model):
    rfid_reader_ip = models.CharField(max_length=50, null=False, blank=False)
    client_device_ip = models.CharField(max_length=15, null=False, blank=False)
    basket_no = models.CharField(max_length=20, null=True)
    is_used = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    pid = models.IntegerField(null=False)
    scan_times = models.FloatField(null=False)
    is_passed = models.BooleanField(default=False)
    is_logged = models.BooleanField(default=False)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='rfid_read_log_create_by')
    create_at = models.DateTimeField(auto_now_add=True, editable=False)

    def clean(self):
        if not self.is_passed:
            if RFID_read_log.objects.filter(basket_no=self.basket_no, is_passed=False).exclude(pk=self.pk).exists():
                raise ValidationError(f"Đã tồn tại trong db")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class scrap_maintain(models.Model):
    yymm = models.CharField(max_length=10,verbose_name='Year + month')
    stockout_form = models.CharField(max_length=30,verbose_name='StockOut Number',)
    batch_no = models.CharField(max_length=25, blank=True, null=True)
    stockout_lack_former = models.IntegerField(verbose_name='Former Lack Amount',default=0)
    stockout_lack_basket = models.IntegerField(verbose_name='Basket Lack Amount',default=0)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                     related_name='scrap_maintain_created_by', null=True,
                                     blank=True
                                     )
    create_at = models.DateTimeField(auto_now_add=True,editable=False)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                     related_name='scrap_maintain_updated_by',
                                     null=True,
                                     blank=True
                                     )
    update_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    class Meta:
        db_table = 'scrap_maintain'
        verbose_name = 'Scrap Maintenance'
        verbose_name_plural = 'Scrap Maintenances'
        ordering = ['-create_at']

    def __str__(self):
        return f"{self.stockout_form} - {self.yymm}"
