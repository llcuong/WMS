$(function(){
    $("ul.subs").hide(); //子選單(ul.subs)隱藏
    $(".main-nav").click(function(){
      $("ul.subs").slideUp();
      $(".main-nav").removeClass("open"); //移除在(.main)的class屬性(open)
      if($("+ul",this).css("display")=="none"){
        $("+ul",this).slideDown();
        $(this).addClass("open"); //被點擊的元素新增一組class(open)
      }
    }).mouseover(function(){
      $(this).addClass("rollover") //滑鼠移入這個元素時新增class(rollover)
    }).mouseout(function(){
      $(this).removeClass("rollover") //滑鼠移開這個元素時移除class(rollover)
    });
    //點擊主選單(.main) 子選單(ul.subs)向上滑動隱藏，移除主選單(.main)的class(open)，如果被點擊的這個元素相鄰的ul display=none 則向下滑動出相鄰的ul並新稱class(open)。
  });