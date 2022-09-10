$(function(){
    $("#login").click(function(){
       var $username = $("#username");
       var $password = $("#password");
       if($username.val() == ""){       
           $username.next().text("please input username!").css({"font-weight":"bold","color":"red"});
           event.preventDefault();      
       }else if($password.val() == ""){
         $password.next().text("please input password").css({"font-weight":"bold","color":"red"});
         event.preventDefault();
       }else{
         $.ajax({
             url:"/user/login",
             type:"post",
             data:{
                 username:$username.val(),
                 password:$password.val()
             },
             success:function(result){
                if(result == "Login Failed"){
                    $username.next().text("username or password wrong").css({"font-weight":"bold","color":"red"});
                    $password.next().text("username or password wrong").css({"font-weight":"bold","color":"red"});
                }else if (result == "Login Success"){
                    window.location.href = "/";
                }
            }
        });
     }
 });
})