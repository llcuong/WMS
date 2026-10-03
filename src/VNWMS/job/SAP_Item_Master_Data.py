import os
import django
from django.utils import timezone
from VNWMS.database import database, sap_database

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VNWMS.settings.test')
django.setup()


class SAP_Item_Master_Data(object):

    def get_sap_item_data(self):
        sap_db = sap_database()

        sql = f"""
          SELECT G1_NAME, MATNR, MAKTX_VI, MAKTX_ZH,SIZE_NAME
          FROM [PMG_SAP].[dbo].[ZMARA] sap
          JOIN [PMGMES].[dbo].[PMG_MES_NBR_SCADA_Std] mes on sap.MATNR = mes.PartNo
        """

        rows = sap_db.select_sql_dict(sql)
        return rows

    def delete_sap_item_data(self):
        vnwms_db = database()

        vnwms_db.execute_sql("""
                DELETE FROM [GDWMS].[dbo].[warehouse_item_master_data]
        """)

    def insert_sap_item_data(self, sap_items):
        vnwms_db = database()
        create_at = timezone.now()
        create_by = 1

        for item in sap_items:
            vnwms_db.execute_sql("""
                INSERT INTO [GDWMS].[dbo].[warehouse_item_master_data] (partno ,product_item ,product_name ,size, 
                update_at, update_by_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                item['MATNR'],
                item['MAKTX_ZH'],
                item['MAKTX_VI'],
                item['SIZE_NAME'],
                create_at,
                create_by
            ])
            # (MATNR, MAKTX_ZH, MAKTX_VI, SIZE_NAME, update_at, update_by_id)

    def main(self):
        # MES SAP Table
        sap_items = self.get_sap_item_data()
        print(sap_items)

        # WMS Table
        self.delete_sap_item_data()
        self.insert_sap_item_data(sap_items)


if __name__ == '__main__':
    c = SAP_Item_Master_Data()
    c.main()