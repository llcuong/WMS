from django.utils.translation import gettext_lazy as _, get_language


def former_search_define():
    column_width = [50, 246, 149, 87, 124, 100, 100, 120, 160, 130, 150, 150, 80]
    column_align = ['right', 'left', 'left', 'center', 'center', 'right', 'right', 'center', 'right', 'center', 'center', 'center', 'center']
    column_name = ['', _('Batch no'), _('Received Form'), _('Size'), _('Brand'), _('Length'), _('Model'), _('Item no'), _('Data date'), _('Used day'), _('Total basket'), _('Total former'), '']
    return column_width, column_align, column_name


def former_stockout_define():
    column_width = [6, 27, 24, 11, 16, 11, 7]
    column_align = ['right', 'left', 'left', 'center', 'center', 'center', 'center']
    column_name = ['', 'Batch', 'Basket', 'Size', 'Brand', 'Used', 'Qty']
    return column_width, column_align, column_name

