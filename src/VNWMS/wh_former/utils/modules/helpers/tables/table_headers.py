from django.utils.translation import gettext_lazy as _

def basket_master_data_table():
    columns = [
        ('', 52, 'right'),
        (_('Basket No'), 320, 'left'),
        (_('Brand'), 220, 'center'),
        (_('Capacity'), 172, 'center'),
        (_('Length'), 150, 'center'),
        (_('Received Date'), 150, 'center'),
        (_('Purchase Order'), 186, 'center'),
        (_('Create Group'), 220, 'center')
    ]

    column_name = [col[0] for col in columns]
    column_width = [col[1] for col in columns]
    column_align = [col[2] for col in columns]

    return column_width, column_align, column_name


def basket_search_table():
    columns = [
        ('', 52, 'right'),
        (_('Basket No'), 260, 'left'),
        (_('Purchase Order'), 186, 'center'),
        (_('Group'), 350, 'center'),
        (_('Used day'), 140, 'center'),
        (_('Size'), 140, 'center'),
        (_('Bin'), 140, 'center'),
        (_('Brand'), 220, 'center'),
        (_('Capacity'), 136, 'center'),
        (_('Received Date'), 150, 'center'),
        (_('Batch'), 140, 'center'),
        (_('Quantity'), 140, 'center'),
        (_('Printed'), 136, 'center'),
        (_('Status'), 220, 'center'),
        (_('Action'), 140, 'center'),
        (_('Description'), 350, 'center'),
    ]

    column_name = [col[0] for col in columns]
    column_width = [col[1] for col in columns]
    column_align = [col[2] for col in columns]

    return column_width, column_align, column_name


def former_master_data_table():
    columns = [
        ('', 52, 'right'),
        (_('Basket No'), 260, 'left'),
        (_('Vendor name'), 220, 'center'),
        (_('Former Qty'), 136, 'center'),
        (_('Bin'), 150, 'center'),
    ]

    column_name = [col[0] for col in columns]
    column_width = [col[1] for col in columns]
    column_align = [col[2] for col in columns]

    return column_width, column_align, column_name


def basket_broken_reporting_table():
    columns = [
        ('', 52, 'right'),
        (_('Basket No'), 260, 'left'),
        (_('Vendor name'), 220, 'center'),
        (_('Former Qty'), 136, 'center'),
        (_('Bin'), 150, 'center'),
    ]

    column_name = [col[0] for col in columns]
    column_width = [col[1] for col in columns]
    column_align = [col[2] for col in columns]

    return column_width, column_align, column_name


def former_broken_reporting_table():
    columns = [
        ('', 52, 'right'),
        (_('Basket No'), 260, 'center'),
        (_('Bin'), 220, 'center'),
        (_('Used Days'), 136, 'center'),
        (_('Former QTY'), 150, 'center'),
        (_('Basket QTY'), 150, 'center')
    ]

    column_name = [col[0] for col in columns]
    column_width = [col[1] for col in columns]
    column_align = [col[2] for col in columns]

    return column_width, column_align, column_name