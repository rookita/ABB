$(function(){
    $("#signup").click(function(){
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
             url:"/user/signup",
             type:"post",
             data:{
                 username:$username.val(),
                 password:$password.val()
             },
             success:function(result){
                if(result == "username already exists!"){
                    alert("username already exists!");
                    window.location.href = "/user/signup"
                }else if (result == "success"){
                    alert("Success!")
                    window.location.href = "/user/login";
                }
            }
        });
     }
 });
})