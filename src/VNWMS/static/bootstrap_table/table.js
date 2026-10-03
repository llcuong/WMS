$.ajaxSetup({
    async : false
});


var createSimpleTable = function (target_div, column_data, page_size, data_url){
    $(target_div).bootstrapTable({
        uniqueId: "ID",
        toolbar: '#toolbar',                //工具按钮用哪个容器
        pageSize:page_size,                       //每页的记录行数（*）
        url: data_url,
        columns: column_data,
        onLoadSuccess: function (res) {
            if(res==''){
                $(target_div).parent().parent().parent().html("<div class='m-3'>目前沒有任何資料!</div>");
            }
        }
    });
}

var createBootstrapTable = function (target_div, column_data, page_size, data_url, sub_data_url){
    $(target_div).bootstrapTable({
        uniqueId: "ID",
        toolbar: '#toolbar',                //工具按钮用哪个容器
        pageSize:page_size,                       //每页的记录行数（*）
        url: data_url,
        detailView: true,
        detailFilter:function(index,row){
            if(row.nested=='0'){
                return false;
            }else{
                return true;
            }
        },
        columns: column_data,
        onExpandRow: function (index, row, $detail) {
            buildChildTable($detail,row);
        },
        onLoadSuccess: function(res) {
            if(res==''){
                $(target_div).parent().parent().parent().html("<div class='m-3'>目前沒有任何資料!</div>");
            }
        }
    });

    var buildChildTable = function ($detail,row){
        $detail.html('<table></table>').find('table').bootstrapTable({
            url: sub_data_url+row.id+'/requests',
            method:"get",
            queryParams:{},
            ajaxOptions:{},
            detailView: true,
            showHeader: true,
            detailFilter:function(index,row){
                if(row.nested=='0'){
                    return false;
                }else{
                    return true;
                }
            },
            columns: column_data,
            onExpandRow: function (index, row, $detail) {
                buildChildTable($detail,row);
            }
        });
    };


};




