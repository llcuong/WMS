from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import get_language


class Plant(models.Model):
    plant_code = models.CharField(primary_key=True, max_length=20)  # Primary key with varchar(20)
    plant_name = models.CharField(max_length=100)  # Name with varchar(100)
    create_at = models.DateTimeField(default=timezone.now)  # Creation timestamp
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='warehouse_plant_create_by')
    update_at = models.DateTimeField(default=timezone.now)  # Last updated timestamp
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='warehouse_plant_update_by')

    def __str__(self):
        return self.plant_name


class Warehouse(models.Model):
    wh_code = models.CharField(primary_key=True, max_length=20)  # Primary key with varchar(20)
    wh_name = models.CharField(max_length=100)  # Name with varchar(100)
    wh_comment = models.CharField(max_length=500, null=True, blank=True)  # Comment, nullable
    wh_plant = models.CharField(max_length=20, null=True, blank=True)
    wh_bg = models.ImageField(upload_to='warehouse_images/', null=True, blank=True)
    wh_packing_func = models.BooleanField(null=True, blank=True, default=False)
    wh_former_func = models.BooleanField(null=True, blank=True, default=False)
    wh_wip_func = models.BooleanField(null=True, blank=True, default=False)
    wh_product_func = models.BooleanField(null=True, blank=True, default=False)
    create_at = models.DateTimeField(default=timezone.now)  # Creation timestamp
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='warehouse_create_by')
    update_at = models.DateTimeField(default=timezone.now)  # Last updated timestamp
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='warehouse_update_by')

    def save(self, *args, **kwargs):
        # Lấy người dùng từ kwargs hoặc từ session nếu không truyền trực tiếp
        user = kwargs.pop('user', None)

        if not self.pk:  # Nếu là bản ghi mới
            if user:
                self.create_by = user  # Gán người dùng vào create_by
                self.create_at = timezone.now()  # Gán thời gian tạo
            else:
                raise ValueError("User must be provided for 'create_by'.")  # Nếu không có người dùng, raise lỗi

        if user:
            self.update_by = user  # Gán người dùng vào update_by
        self.update_at = timezone.now()  # Cập nhật thời gian update

        super().save(*args, **kwargs)  # Gọi phương thức save của lớp cha

    def __str__(self):
        return self.wh_code  # Human-readable string representation


class Area(models.Model):
    area_id = models.CharField(max_length=20, unique=True, primary_key=True)
    area_name = models.CharField(max_length=100)
    warehouse = models.ForeignKey(Warehouse, related_name='area_warehouse', on_delete=models.CASCADE)
    pos_x = models.IntegerField(blank=True, null=True)  # Toạ độ X, có thể null
    pos_y = models.IntegerField(blank=True, null=True)  # Toạ độ Y, có thể null
    area_w = models.IntegerField(blank=True, null=True)  # Bin Width
    area_l = models.IntegerField(blank=True, null=True)  # Bin Length
    layer = models.CharField(max_length=10, blank=True, null=True)
    create_at = models.DateTimeField(default=timezone.now)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='area_create_by')
    update_at = models.DateTimeField(default=timezone.now)  # Tự động cập nhật thời gian mỗi khi bản ghi được cập nhật
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='area_update_by')

    def save(self, *args, **kwargs):
        # Lấy người dùng từ kwargs hoặc từ session nếu không truyền trực tiếp
        user = kwargs.pop('user', None)

        if not self.pk:  # Nếu là bản ghi mới
            if user:
                self.create_by = user  # Gán người dùng vào create_by
                self.create_at = timezone.now()  # Gán thời gian tạo
            else:
                raise ValueError("User must be provided for 'create_by'.")  # Nếu không có người dùng, raise lỗi

        if user:
            self.update_by = user  # Gán người dùng vào update_by
        self.update_at = timezone.now()  # Cập nhật thời gian update

        super().save(*args, **kwargs)  # Gọi phương thức save của lớp cha

    def __str__(self):
        return self.area_id


class Bin(models.Model):
    bin_id = models.CharField(max_length=20, unique=True, primary_key=True)
    bin_name = models.CharField(max_length=100)
    area = models.ForeignKey(Area, related_name='bin_area', on_delete=models.CASCADE)  # Liên kết với bảng Area
    create_at = models.DateTimeField(default=timezone.now)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='bin_create_by')
    update_at = models.DateTimeField(default=timezone.now)  # Tự động cập nhật thời gian mỗi khi bản ghi được cập nhật
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='bin_update_by')

    def save(self, *args, **kwargs):
        # Lấy người dùng từ kwargs hoặc từ session nếu không truyền trực tiếp
        user = kwargs.pop('user', None)

        if not self.pk:  # Nếu là bản ghi mới
            if user:
                self.create_by = user  # Gán người dùng vào create_by
                self.create_at = timezone.now()  # Gán thời gian tạo
            else:
                raise ValueError("User must be provided for 'create_by'.")  # Nếu không có người dùng, raise lỗi

        if user:
            self.update_by = user  # Gán người dùng vào update_by
        self.update_at = timezone.now()  # Cập nhật thời gian update

        super().save(*args, **kwargs)  # Gọi phương thức save của lớp cha

    def __str__(self):
        return self.bin_id


class MovementType(models.Model):
    mvt_code = models.CharField(max_length=20, primary_key=True)
    mvt_name = models.CharField(max_length=20, blank=False, null=False)
    mvt_vn_name = models.CharField(max_length=20, blank=True, null=True)
    desc = models.CharField(max_length=200, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, editable=True)  # 建立日期
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='mvt_create_by')  # 建立者

    def get_translated_name(self):
        lang = get_language()
        if lang == 'vi' and self.mvt_vn_name:
            return self.mvt_vn_name
        elif lang == 'zh-hant' and self.desc:
            return self.desc
        return self.mvt_name

    def __str__(self):
        return self.mvt_code


class ItemType(models.Model):
    type_code = models.CharField(max_length=20, primary_key=True)
    type_name = models.CharField(max_length=20, blank=False, null=False)
    type_vn_name = models.CharField(max_length=20, blank=True, null=True)
    desc = models.CharField(max_length=200, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, editable=True)  # 建立日期
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='itemtype_create_by')  # 建立者

    def get_item_type_name(self):
        lang = get_language()
        if lang == 'vi' and self.type_vn_name:
            return self.type_vn_name
        elif lang == 'zh-hant' and self.type_name:
            return self.type_name
        return self.type_code

    def __str__(self):
        return self.desc


class UnitType(models.Model):
    unit_code = models.CharField(max_length=20, primary_key=True)
    unit_name = models.CharField(max_length=20, blank=False, null=False)
    desc = models.CharField(max_length=200, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, editable=True)  # 建立日期
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                                  related_name='unittype_create_by')  # 建立者

    def __str__(self):
        return self.desc


class Item_Master_Data(models.Model):
    partno = models.CharField(max_length=24, primary_key=True)
    product_item = models.CharField(max_length=50, null=False, blank=False)
    product_name = models.CharField(max_length=50, null=False, blank=False)
    size = models.CharField(max_length=10, null=False, blank=True)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    update_at = models.DateTimeField(default=timezone.now)