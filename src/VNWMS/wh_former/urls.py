from django.urls import re_path as url
from wh_former.utils.settings.settings import manage_add_new_client, manage_delete_client, manage_connection_test_client, \
    manage_edit_client, manage_power_client, update_control_location

from wh_former.views import user_basket_master_data, user_basket_search, user_basket_modify, user_former_master_data, \
    user_former_search, user_former_stock_in, user_former_stock_out, user_batch_histoty, user_batch_action_history, \
    former_transaction, scrap_to_excel, basket_broken_reporting, former_broken_reporting, basket_broken_get_data, \
    user_former_stock_in_empty, user_former_stock_out_empty

from wh_former.utils.api.rfid_uhf_api import rfid_start_reader_api, rfid_stop_reader_api, rfid_clear_reader_api
from wh_former.utils.api.former_api import get_batch_no_api,former_batch_detail_api, get_rack_bin_temp, \
    delete_rack_temp, get_rack_stats, get_area_data_api, former_batch_update_api, former_batch_full_detail_api, \
    former_batch_update_bin_api, batch_data_confirm_scrap, uhf_basket_data_api, uhf_stock_out_basket_data_api
from wh_former.utils.api.rfid_epc_api import set_epc_is_passed, get_rfid_epc_api, get_rfid_epc_data_api, rfid_print_api, get_stockform_bin_api
from wh_former.utils.api.area_bin_api import bin_selection_api, get_area_batch_info
from wh_former.utils.api.parameter_data_api import enable_param_api, disable_param_api, delete_param_api, edit_param_api
from wh_former.utils.api.stock_form_api import get_machine_by_plant_api, get_line_by_machine_api, get_wo_by_line_api, \
    get_stockin_choice_api, get_lost_basket_api, get_stockout_forms_api, print_total_former_on_select_api, generate_stock_form_api, get_plant_by_mode_api
from wh_former.utils.api.item_decode_api import decode_item_number_api

from wh_former.utils.modules.api.basket.basket_master_data import basket_master_data_preview, delete_basket_master_data, \
    check_purchase_order_data, check_former_form_data


from wh_former.utils.helpers.basket_button import export_excel_button_api, basket_disable_button_api
from wh_former.utils.settings.settings import manage_setting, manage_setting_device_add_new



urlpatterns = [
    url(r'^rfid/(?P<id>\d+)/start/$', rfid_start_reader_api, name='rfid_start_reader'),
    url(r'^rfid/(?P<id>\d+)/stop/$', rfid_stop_reader_api, name='rfid_stop_reader'),
    url(r'^rfid/clear$', rfid_clear_reader_api, name='rfid_clear_reader'),

    url(r'^rfid/batch$', get_batch_no_api, name='get_batch_no_api'),
    url(r'^rfid/basket$', former_batch_detail_api, name='former_batch_detail_api'),
    url(r'^rfid/basket/update$', former_batch_update_api, name='former_batch_update_api'),
    url(r'^rfid/basket/full$', former_batch_full_detail_api, name='former_batch_full_detail_api'),
    url(r'^rfid/basket/bin/update$', former_batch_update_bin_api, name='former_batch_update_bin_api'),
    url(r'^rfid/scrap/batch$', batch_data_confirm_scrap, name='batch_data_confirm_scrap'),
    url(r'^rfid/rack$', get_rack_bin_temp, name='get_rack_bin_temp'),
    url(r'^rfid/delete$', delete_rack_temp, name='delete_rack_temp'),
    url(r'^rfid/stats$', get_rack_stats, name='get_rack_stats'),
    url(r'^rfid/area$', get_area_data_api, name='get_area_data_api'),

    url(r'^rfid/get$', get_rfid_epc_api, name='get_rfid_epc_api'),
    url(r'^rfid/data$', get_rfid_epc_data_api, name='get_rfid_epc_data_api'),
    url(r'^rfid/print$', rfid_print_api, name='rfid_print_api'),
    url(r'^rfid/bin$', get_stockform_bin_api, name='get_stockform_bin_api'),

    url(r'^rfid/batch_drop', decode_item_number_api, name='decode_item_number_api'),

    url(r'^stock/bin', bin_selection_api, name='bin_selection_api'),
    url(r'^area/info', get_area_batch_info, name='get_area_batch_info'),

    url(r'^param/enable', enable_param_api, name='enable_param_api'),
    url(r'^param/disable', disable_param_api, name='disable_param_api'),
    url(r'^param/delete', delete_param_api, name='delete_param_api'),
    url(r'^param/edit', edit_param_api, name='edit_param_api'),

    url(r'^get/plants/$', get_plant_by_mode_api, name='get_plant_by_mode_api'),
    url(r'^get/machines/$', get_machine_by_plant_api, name='get_machine_by_plant_api'),
    url(r'^get/lines/$', get_line_by_machine_api, name='get_line_by_machine_api'),
    url(r'^get/wo/$', get_wo_by_line_api, name='get_wo_by_line_api'),
    url(r'^get/in/$', get_stockin_choice_api, name='get_stockin_choice_api'),
    url(r'^get/epc/$', get_lost_basket_api, name='get_lost_basket_api'),
    url(r'^get/forms/$', get_stockout_forms_api, name='get_stockout_forms_api'),

    url(r'^basket/excel$', export_excel_button_api, name='export_excel_button_api'),
    url(r'^basket/disable', basket_disable_button_api, name='basket_disable_button_api'),

    url(r'^basket/preview$', basket_master_data_preview, name='basket_master_data_preview'),
    url(r'^basket/delete$', delete_basket_master_data, name='delete_basket_master_data'),
    url(r'^basket/po_check$', check_purchase_order_data, name='check_purchase_order_data'),
    url(r'^former/po_check$', check_former_form_data, name='check_former_form_data'),







    url(r'^rfid/clear$', rfid_clear_reader_api, name='rfid_clear_reader'),
    url(r'^rfid/exit$', set_epc_is_passed, name='set_epc_is_passed'),






    url(r'^basket/search$', user_basket_search, name='basket_search'),
    url(r'^basket/edit$', user_basket_modify, name='basket_modify'),
    url(r'^former/insert', user_former_master_data, name='former_insert'),
    url(r'^former/search$', user_former_search, name='former_search'),
    url(r'^former/in$', user_former_stock_in, name='former_in'),
    url(r'^former/in_empty$', user_former_stock_in_empty, name='former_in_empty'),
    url(r'^former/out$', user_former_stock_out, name='former_out'),
    url(r'^former/out_empty$', user_former_stock_out_empty, name='former_out_empty'),
    url(r'^batch/history', user_batch_histoty, name='batch_history'),
    url(r'^batch/action$', user_batch_action_history, name='batch_action_history'),





    url(r'^manage/', manage_setting, name='actions'),
    url(r'^manage/', manage_setting_device_add_new, name='manage_wh_former_index'),

    url(r'^manage_client_add', manage_add_new_client, name='manage_wh_former_add_new_client'),
    url(r'^manage_client_delete/(?P<id>\d+)/$', manage_delete_client, name='manage_wh_former_delete_client'),
    url(r'^update_control_location$', update_control_location, name='update_control_location'),
    url(r'^manage_client_edit/(?P<id>\d+)/$', manage_edit_client, name='manage_wh_former_edit_client'),
    url(r'^manage_client_connection_test/(?P<id>\d+)/$', manage_connection_test_client, name='manage_wh_former_connection_test_client'),
    url(r'^manage_client_power/(?P<id>\d+)/$', manage_power_client, name='manage_wh_former_power_client'),

    url(r'^stock_form/print_total_former/$', print_total_former_on_select_api, name='print_total_former_on_select_api'),
    url(r'^stock_form/get/$', generate_stock_form_api, name='generate_stock_form_api'),


    # Former warehouse transaction
    url(r'^transaction$', former_transaction, name='wh_former_transaction'),
    url(r'^transaction/excel$', scrap_to_excel, name='former_scrap_excel'),
    url(r'^transaction/basket/data$', basket_broken_get_data, name='basket_broken_get_data'),
    url(r'^transaction/basket$', basket_broken_reporting, name='basket_broken_reporting'),
    url(r'^transaction/former', former_broken_reporting, name='former_broken_reporting'),

    # UHF APIs --- 0.0.0.0:8000/wh_former/uhf
    url(r'^uhf/basket$', uhf_basket_data_api, name='uhf_basket_data_api'),
    url(r'^uhf/basket/stock_out$', uhf_stock_out_basket_data_api, name='uhf_stock_out_basket_data_api'),


    url(r'^', user_basket_master_data, name='basket_insert'),
]