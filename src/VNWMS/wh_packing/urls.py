from django.urls import re_path as url
from wh_packing.views import check_po_exists, open_data_import, open_data_import_api, open_data_import_confirm_api, \
    bin_search, get_areas, get_bins, get_bin_data, check_bin_exists, inventory_sheet, inventory_delete, \
    inventory_deletion, stockin_form, get_product_order_info, get_product_order_stout, get_purchase_no_stout, \
    get_purchase_no_info, packing_material_stock_in, packing_material_stock_out, packing_material_stock_in_post, \
    packing_material_stock_out_post, dashboard, import_excel_data, product_order_hist_data, product_order_search, \
    product_order_bin_search, transfer_and_adjust, bin_transfer_page, bin_transfer, bin_adjust_page, bin_adjust, \
    warehouse_map, download_excel_template, get_all_areas, get_product_order_stout, trans_hist_top100, sap_import, \
    sap_query, sap_query_api, recover_stock, get_hist_data, get_info_by_batch, order_problem_page, order_problem, \
    update_user_plant

urlpatterns = [
    url(r'^get_all_areas/$', get_all_areas, name='get_all_areas_api'),
    url(r'^check_po_exists/$', check_po_exists, name='check_po_exists'),
    url(r'^open_data_import/$', open_data_import, name="open_data_import"),
    url(r'^open_data_import_api/$', open_data_import_api, name="open_data_import_api"),
    url(r'^open_data_import_confirm_api/$', open_data_import_confirm_api, name="open_data_import_confirm_api"),
    url(r'^sap_import/$', sap_import, name="sap_import"),
    url(r'^sap_query/$', sap_query, name="sap_query"),
    url(r'^sap_query_api/$', sap_query_api, name="sap_query_api"),


    url(r'^bin/search/$', bin_search, name='bin_search'),
    url(r'^get_areas/$', get_areas, name='get_areas'),
    url(r'^get_bins/$', get_bins, name='get_bins'),
    url(r'^get_bin_data/$', get_bin_data, name='get_bin_data'),
    url(r'^check_bin_exists/$', check_bin_exists, name='check_bin_exists'),

    url(r'^update_user_plant/$', update_user_plant, name='update_user_plant'),

    url(r'^inventory_sheet/$', inventory_sheet, name="inventory_sheet"),
    url(r'^inventory_delete/$', inventory_delete, name="inventory_delete"),
    url(r'^recover_stock/$', recover_stock, name="recover_stock"),
    # url(r'^get_info_by_batch/$', get_info_by_batch, name="get_info_by_batch"),
    url(r'^get_hist_data/$', get_hist_data, name="get_hist_data"),
    url(r'^inventory_deletion/$', inventory_deletion, name="inventory_deletion"),

    url(r'^stockin_form/(?P<pk>\w+)/$', stockin_form, name='stockin_form'),
    url(r'^get_product_order_info/', get_product_order_info, name='get_product_order_info'),
    url(r'^get_product_order_stout/', get_product_order_stout, name='get_product_order_stout'),
    url(r'^get_purchase_no_stout/', get_purchase_no_stout, name='get_purchase_no_stout'),
    url(r'^get_purchase_no_info/', get_purchase_no_info, name='get_purchase_no_info'),
    url(r'^packing_material_stock_in/', packing_material_stock_in, name='packing_material_stock_in'),
    url(r'^packing_material_stock_out/', packing_material_stock_out, name='packing_material_stock_out'),
    url(r'^packing_material_stock_in_post/', packing_material_stock_in_post, name='packing_material_stock_in_post'),
    url(r'^packing_material_stock_out_post/', packing_material_stock_out_post, name='packing_material_stock_out_post'),
    url(r'^dashboard/', dashboard, name='warehouse_dashboard'),
    url(r'^upload/$', import_excel_data, name="import_excel_data"),

    url(r'^product_order_search/$', product_order_search, name='product_order_search'),
    url(r'^product_order_hist_data/$', product_order_hist_data, name='product_order_hist_data'),
    url(r'^product_order_hist100_data/$', product_order_hist_data, name='product_order_hist100_data'),
    url(r'^product_order_bin_search/$', product_order_bin_search, name='product_order_bin_search'),
    url(r'^trans_hist_top100/$', trans_hist_top100, name='trans_hist_top100'),
    url(r'^transfer_and_adjust/$', transfer_and_adjust, name='transfer_and_adjust'),
    url(r'^bin_transfer_page/$', bin_transfer_page, name='bin_transfer_page'),
    url(r'^bin/transfer/$', bin_transfer, name='bin_transfer'),
    url(r'^bin_adjust_page/$', bin_adjust_page, name='bin_adjust_page'),
    url(r'^bin/adjust/$', bin_adjust, name='bin_adjust'),
    url(r'^map/(?P<pk>\w+)/$', warehouse_map, name='warehouse_map'),
    url(r'^download-template/(?P<filename>[\w\-.]+)/$', download_excel_template, name='download_excel_template'),
    url(r'^order_problem_page/$', order_problem_page, name='order_problem_page'),
    url(r'^order_problem/$', order_problem, name='order_problem'),

]




