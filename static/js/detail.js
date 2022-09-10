$(function(){
    $("#submit").click(function(){
       var $bid = $("#bid");
       var $nonce = $("#nonce");
       var $password = $("#password");
       var $addr = $("#addr");      
        $.ajax({
            url:"/auction/participate",
            type:"post",
            data:{
                bid:$bid.val(),
                nonce:$nonce.val(),
                addr:$addr.val(),
                password:$password.val()
            },
            success:function(result){
            if(result == "password wrong"){
                    $password.next().text("password wrong").css({"font-weight":"bold","color":"red"});
                }else if (result == "auction end"){
                    window.alert("the auction is ended")
                    window.location.href = "/auction/view";
                }
                else if (result == "success"){
                    window.alert("Success!")
                    window.location.href = "/auction/view";
                }
            }
        });
    });
 });