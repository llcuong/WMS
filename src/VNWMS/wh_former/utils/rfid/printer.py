import os
import clr
from System.Collections.Generic import List
from wh_former.models import Basket_master_data, Basket_master_data_print_log
from django.db.models import F

DLL_PATH = os.path.join(os.path.abspath(os.path.abspath(".")), "wh_former", "utils", "rfid", "print.dll")


def _load_printer_dll(dll_path):
    path = os.path.abspath(dll_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy DLL tại: {path}")
    clr.AddReference(path)
    from LabelPrinter import ZMPrinter, ZMLabel
    return ZMPrinter(), ZMLabel()


def define_label(printer, label, obj_list):
    printer.printername = "X1iD"
    printer.printerdpi = 300
    printer.printSpeed = 4
    printer.printDarkness = 10
    printer.labelhavegap = True

    label.labelwidth = 44  # 75
    label.labelheight = 19  # 20
    label.labelrowgap = 1  # 2

    obj_list.clear()
    # TODO: thêm các LabelObject tĩnh (text, barcode…) nếu cần


def net_print_and_write(label_value, epc_value, printer_ip):
    printer, label = _load_printer_dll(DLL_PATH)
    label_value = label_value
    epc_value = epc_value

    from LabelPrinter import LabelObject, PrintUtility, PrinterStyle

    printer.printerinterface = PrinterStyle.NET
    printer.printernetip = printer_ip

    printer.printername = "X1iD"
    printer.printerdpi = 300
    printer.printSpeed = 4
    printer.printDarkness = 20
    printer.labelhavegap = True

    label.labelwidth = 44
    label.labelheight = 19
    label.labelrowgap = 1

    objs = []

    # textobject01 = LabelObject()
    # textobject01.ObjectName = "text-01"
    # textobject01.objectdata = f'{epc_value}'
    # textobject01.Xposition = 4
    # textobject01.Yposition = 6
    # textobject01.texttextalign = 0
    # textobject01.texttextvalign = 1
    # textobject01.texttype = 1
    # textobject01.textwidth = 50.0
    # textobject01.textwidthbeyound = 0
    # textobject01.textfont = "Arial"
    # textobject01.fontstyle = 1
    # textobject01.fontsize = 12
    # objs.append(textobject01)

    barcodeobject01 = LabelObject()
    barcodeobject01.ObjectName = "barcode-01"
    barcodeobject01.objectdata = label_value
    barcodeobject01.Xposition = 1  # 2
    barcodeobject01.Yposition = 3
    barcodeobject01.barcodekind = "Code 128 Auto"
    barcodeobject01.barcodescale = 4
    barcodeobject01.barcodeheight = 8
    objs.append(barcodeobject01)

    # textobject02 = LabelObject()
    # textobject02.ObjectName = "text-02"
    # textobject02.objectdata = f'{epc_value[1]}'
    # textobject02.Xposition = 5
    # textobject02.Yposition = 16
    # textobject02.texttextalign = 0
    # textobject02.texttextvalign = 1
    # textobject02.texttype = 1
    # textobject02.textwidth = 50.0
    # textobject02.textwidthbeyound = 0
    # textobject02.textfont = "Arial"
    # textobject02.fontstyle = 1
    # textobject02.fontsize = 8
    # objs.append(textobject02)

    rfid = LabelObject()
    rfid.ObjectName = "rfiduhf-01"
    rfid.objectdata = epc_value
    rfid.RFIDDatablock = 0
    rfid.RFIDDatatype = 1
    rfid.RFIDerrortimes = 1
    objs.append(rfid)

    print(f'label_value--print - {label_value}')
    print(f'epc_value--print - {epc_value}')
    print(f'objs--print - {objs}')

    net_list = List[LabelObject]()
    for o in objs:
        net_list.Add(o)

    result = PrintUtility().PrintLabel(printer, label, net_list, True, True)
    # print('P---R---I---N---T--E--D')
    if result and result.startswith("Error:"):
        raise RuntimeError(result)

    if epc_value != '-':
        epc_value = epc_value
        basket = Basket_master_data.objects.filter(basket_no=epc_value).first()
        is_first_print = basket.is_print == 0

        updated = Basket_master_data.objects.filter(basket_no=epc_value).update(
            is_print=F('is_print') + 1
        )

        if updated == 1 and is_first_print:
            Basket_master_data_print_log.objects.filter(basket_purchase_order=basket.basket_purchase_order).update(
                basket_printed_qty=F('basket_printed_qty') + 1
            )

        if updated == 0:
            print(f"Không tìm thấy basket_no: {epc_value}")


    return result #'打印完成(Print finished).'


def net_print_and_write_list(current_label_list, current_epc_list, printer_ip: str):
    results = {}
    for i in range(len(current_epc_list)):
        try:
            # print(f'IN LẦN {i+1}')
            # print(f'labels ------ > {current_label_list[i]}')
            res = net_print_and_write(current_label_list[i], current_epc_list[i], printer_ip)
            results[current_epc_list[i]] = res or "Success"
        except Exception as e:
            # print(f"ERROR -: {e}")
            results[current_epc_list[i]] = str(e)
            pass

    return results
