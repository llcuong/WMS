from django.db import connections


class database:
    def execute_sql(self, sql):
        with connections['default'].cursor() as cur:
            cur.execute(sql)

    def select_sql(self, sql):
        with connections['default'].cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def select_sql_dict(self, sql):
        with connections['default'].cursor() as cur:
            cur.execute(sql)

            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data


class sap_database:
    def select_sql(self, sql):
        with connections['SAP'].cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def select_sql_dict(self, sql):
        with connections['SAP'].cursor() as cur:
            cur.execute(sql)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def execute_sql(self, sql):
        with connections['SAP'].cursor() as cur:
            cur.execute(sql)


class mes_database:
    def select_sql(self, sql):
        with connections['MES'].cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def select_sql_dict(self, sql):
        with connections['MES'].cursor() as cur:
            cur.execute(sql)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def select_sql_dict_param(self, sql, param):
        with connections['MES'].cursor() as cur:
            cur.execute(sql, param)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def execute_sql(self, sql):
        with connections['MES'].cursor() as cur:
            cur.execute(sql)



class lkwms_database:
    def select_sql(self, sql):
        with connections['LKWMS'].cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def select_sql_dict(self, sql):
        with connections['LKWMS'].cursor() as cur:
            cur.execute(sql)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    def select_sql_dict_param(self, sql, param):
        with connections['LKWMS'].cursor() as cur:
            cur.execute(sql, param)
            desc = cur.description
            column_names = [col[0] for col in desc]
            data = [dict(zip(column_names, row))
                    for row in cur.fetchall()]
            return data

    # def execute_sql(self, sql):
    #     with connections['VNWMS'].cursor() as cur:
    #         cur.execute(sql)

    def execute_sql(self, sql, params=None):
        with connections['LKWMS'].cursor() as cur:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)