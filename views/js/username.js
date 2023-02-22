$(document).ready(function(){
    var user_data = sessionStorage.getItem("current_user_data");

    if(!(user_data === null)){
        var user_data_json = JSON.parse(user_data);

        $(".login-link").hide()
        $(".name-link").html(user_data_json["name"]);
    } else {
        $(".name-link").hide()

        if(!location.href.endsWith("login.html")) {
            location.href = "login.html"
        }
    }

    $(".name-link").click(function(){
        sessionStorage.setItem("current_user_data", null);
        location.href = "login.html"
    });
});
