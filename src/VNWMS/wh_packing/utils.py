from datetime import datetime

from django.contrib.auth.decorators import login_required

from VNWMS.database import database
from warehouse.models import MovementType, Bin, ItemType
from warehouse.utils import get_item_type_name
from wh_packing.models import Bin_Value_History, Bin_Value


def Do_Transaction(request, form_no, warehouse, product_order, purchase_no, version_no, version_seq, item_code, size, mvt,
                   bin_code, qty, purchase_unit, desc, stockin_form=None, stockout_form=None, lot=None):

    qty = float(qty)
    bin = Bin.objects.get(bin_id=bin_code)
    mvt = MovementType.objects.get(mvt_code=mvt)
    item_type = ItemType.objects.get(type_code=item_code)
    purchase_no = str(purchase_no)

    result = None

    if purchase_no == None or str(purchase_no) == '':
        purchase_no = 'NA'

    if bin and product_order and purchase_no and warehouse:
        # 更新庫存資料
        invs = Bin_Value.objects.filter(warehouse=warehouse, product_order=product_order, purchase_no=purchase_no, version_no=version_no,
                                        version_seq=version_seq, item_type=item_type, size=size, bin=bin)
        if invs:
            remain_qty = int(invs.first().qty) + qty
        else:
            remain_qty = qty

        if remain_qty >= 0:
            if remain_qty == 0:
                Bin_Value.objects.filter(warehouse=warehouse, product_order=product_order, purchase_no=purchase_no,
                                         version_no=version_no,
                                         version_seq=version_seq,
                                         item_type=item_type,
                                         size=size, bin=bin).delete()
            else:
                tmp1 = {}
                if stockin_form:
                    tmp1 = {'stockin_form': stockin_form}
                if stockout_form:
                    tmp1 = {'stockout_form': stockout_form}

                tmp = {'qty': remain_qty, 'purchase_unit': purchase_unit, 'update_by': request.user}
                tmp.update(tmp1)
                Bin_Value.objects.update_or_create(warehouse=warehouse, product_order=product_order, purchase_no=purchase_no,
                                                   version_no=version_no,
                                                   version_seq=version_seq,
                                                   item_type=item_type,
                                                   size=size, bin=bin,
                                                   defaults=tmp)

            if qty > 0:
                Bin_Value_History.objects.create(batch_no=form_no, warehouse=warehouse, product_order=product_order,
                                                 purchase_no=purchase_no, version_no=version_no,
                                                 version_seq=version_seq, item_type=item_type,
                                                 size=size, bin=bin, mvt=mvt, plus_qty=qty,
                                                 minus_qty=0, remain_qty=remain_qty, comment=desc,
                                                 purchase_unit=purchase_unit,
                                                 create_by=request.user)
            else:
                Bin_Value_History.objects.create(batch_no=form_no, warehouse=warehouse, product_order=product_order,
                                                 purchase_no=purchase_no, version_no=version_no,
                                                 version_seq=version_seq, item_type=item_type,
                                                 size=size, bin=bin, mvt=mvt, plus_qty=0,
                                                 minus_qty=-qty, remain_qty=remain_qty,
                                                 purchase_unit=purchase_unit,
                                                 comment=desc, create_by=request.user)
            result = "DONE"
        else:
            msg = '無庫存可以扣帳'
            print(msg)
            raise ValueError(msg)

    return result


def inventory_search(warehouse=None, area=None, location=None, product_order=None, purchase_order=None, size=None,
                     lot_no=None, version_no=None, item_type=None, route_name=None):
    db = database()

    item_type_name = get_item_type_name()
    extra1 = "extra1"

    sql = f"""
            SELECT distinct b.id
                  ,w.wh_name
                  ,w.wh_plant
                  ,b.product_order
                  ,b.size
                  ,b.qty
                  ,b.bin_id
                  ,bin.bin_name
                  ,b.purchase_no
                  ,b.version_no
                  ,b.version_seq
                  ,b.purchase_unit
                  ,customer_no
                  ,supplier
                  ,lot_no
                  ,purchase_qty
                  ,b.purchase_unit
                  ,{item_type_name} item_type
                  ,post_date
                  ,sap_mtr_no
                  ,d.[desc]
                  {extra1}
            FROM [wh_packing_bin_value] b
            JOIN [warehouse_bin] bin on b.bin_id = bin.bin_id
            JOIN [warehouse_area] area on bin.area_id = area.area_id
            JOIN [wh_packing_stockinform] d on b.stockin_form = d.form_no 
                and b.bin_id = d.order_bin_id
                and b.product_order = d.product_order 
                and b.version_no = d.version_no 
                and b.item_type_id = d.item_type_id
                and b.size = d.size 
            JOIN [warehouse_itemtype] item on b.item_type_id = item.type_code
            JOIN [warehouse_warehouse] w on w.wh_code = area.warehouse_id
            WHERE qty > 0
            """

    if warehouse:
        sql += f" AND b.warehouse_id = '{warehouse}'"

    if product_order:
        sql += f" AND b.product_order LIKE '{product_order}%'"

    if purchase_order:
        sql += f" AND b.purchase_no = '{purchase_order}'"

    if lot_no:
        sql += f" AND d.lot_no = N'{lot_no}'"

    if version_no:
        sql += f" AND d.version_no LIKE N'{version_no}%'"

    if item_type:
        sql += f" AND d.item_type_id = '{item_type}'"

    if area:
        sql += f" AND area.area_id = '{area}'"

    if location:
        sql += f" AND bin.bin_id LIKE '{location}%'"

    if size:
        sql += f" AND b.size LIKE '{size}%'"

    if route_name == "inventory_sheet" and warehouse == 'PVCPKG':

        extra1 = f"""
            ,LEFT(bin.bin_name, CHARINDEX('-', bin.bin_name) - 1) AS part1
            ,CAST(SUBSTRING(bin.bin_name,CHARINDEX('-', bin.bin_name) + 1,
            LEN(bin.bin_name) - CHARINDEX('-', bin.bin_name) - 1
            ) AS INT) AS part2
            ,RIGHT(bin.bin_name, 1) AS part3
        """
        sql = sql.replace("extra1", extra1)
        sql += f"""
            ORDER BY part1, part2, part3;
        """
    else:
        extra1 = ""
        sql = sql.replace("extra1", extra1)
    results = db.select_sql_dict(sql)

    return results


def inventory_id_search(warehouse=None, area=None, location=None, product_order=None, purchase_order=None,
                            size=None, lot_no=None, version_no=None, item_type=None):
    db = database()

    sql = f"""
            SELECT b.id

            FROM [wh_packing_bin_value] b
            JOIN [warehouse_bin] bin on b.bin_id = bin.bin_id
            JOIN [warehouse_area] area on bin.area_id = area.area_id
            JOIN [wh_packing_stockinform] d on b.stockin_form = d.form_no 
                and b.bin_id = d.order_bin_id
                and b.product_order = d.product_order 
                and b.version_no = d.version_no 
                and b.item_type_id = d.item_type_id
                and b.size = d.size 
            JOIN [warehouse_itemtype] item on b.item_type_id = item.type_code
            JOIN [warehouse_warehouse] w on w.wh_code = area.warehouse_id
            WHERE qty > 0
            """

    if warehouse:
        sql += f" AND b.warehouse_id = '{warehouse}'"

    if product_order:
        sql += f" AND b.product_order LIKE '{product_order}%'"

    if purchase_order:
        sql += f" AND b.purchase_no = '{purchase_order}'"

    if lot_no:
        sql += f" AND d.lot_no = '{lot_no}'"

    if version_no:
        sql += f" AND d.version_no = '{version_no}'"

    if item_type:
        sql += f" AND d.item_type_id = '{item_type}'"

    if area:
        sql += f" AND area.area_id = '{area}'"

    if location:
        sql += f" AND bin.bin_id LIKE '{location}%'"

    if size:
        sql += f" AND b.size LIKE '{size}%'"

    results = db.select_sql_dict(sql)

    return results


def inventory_history(warehouse, location=None, product_order=None, purchase_order=None, size=None,
                      version_no=None, item_type=None,
                      from_date=None, to_date=None):
    bin_hists = Bin_Value_History.objects.filter()

    if warehouse:
        bin_hists = bin_hists.filter(warehouse__wh_code=warehouse)
    if location:
        bin_hists = bin_hists.filter(bin__bin_id__startswith=location)
    if product_order:
        bin_hists = bin_hists.filter(product_order__startswith=product_order)
    if purchase_order:
        bin_hists = bin_hists.filter(purchase_no__startswith=purchase_order)
    if size:
        bin_hists = bin_hists.filter(size__startswith=size)
    if version_no:
        bin_hists = bin_hists.filter(version_no__startswith=version_no)
    if item_type:
        bin_hists = bin_hists.filter(item_type=item_type)
    if from_date:
        start_datetime = datetime.combine(from_date, datetime.min.time())
        bin_hists = bin_hists.filter(create_at__gte=start_datetime)
    if to_date:
        end_datetime = datetime.combine(to_date, datetime.max.time())
        bin_hists = bin_hists.filter(create_at__lte=end_datetime)

    return bin_hists
















