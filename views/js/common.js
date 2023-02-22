function fetch_searched_products(jsonData, table_selector) {
    $.ajax({
        url: "http://127.0.0.1:5050/search_products",
        type: "POST",
        data: JSON.stringify(jsonData),
        contentType:"application/json",
        dataType: 'json',
        success: function(response) {
            if(response.length == 0) {
                $("#"+ table_selector +" tbody").html('<tr><td colspan="4" style="text-align:center;">No Products Found</td></tr>');
            } else {
                $("#"+ table_selector +" tbody").html('');
            }

            for(var index in response) {
                var item = response[index];

                var htmlContent;

                if(table_selector == "product-table") {
                    htmlContent = '<tr>' +
                                  '<td><a href="product.html?product_id=' + item['product_id'] + '">' + item['name'] + '</a></td>' +
                                  '<td>' + item['price'] + '₹</td>' +
                                  '<td>' + item['rating'] + '</td>' +
                                  '<td><button class="btn btn-primary" onclick="addToCart(\''+ item['product_id'] +'\')">Add to Cart</button></td>' +
                                  '</tr>';
                } else if(table_selector == "product-suggestion-table") {
                    htmlContent = '<tr>' +
                                  '<td><a href="product.html?product_id=' + item['product_id'] + '">' + item['name'] + '</a></td>' +
                                  '<td>' + item['price'] + '₹</td>' +
                                  '</tr>';
                }

                $("#"+ table_selector +" tbody").append(htmlContent);
            }
        }
    });
}

function find_suggested_products() {
    var user_data = sessionStorage.getItem("current_user_data");

    var user_id = "";
    if(!(user_data === null)) {
        var user_data_json = JSON.parse(user_data);
        user_id = user_data_json["user_id"]
    }

    $.ajax({
        url: "http://127.0.0.1:5050/fetch_suggestions/" + user_id,
        type: "GET",
        data: "json",
        success: function(response) {
            var jsonData = {
                                "query": "",
                                "start_price": response['start_price'],
                                "end_price": response['end_price'],
                                "rating": 0,
                                "category": response['category']
                           }
            $("#suggested-category").html(response['category']);
            $("#suggested-price-range").html(response['start_price'] + "₹ to " + response['end_price'] + "₹");

            fetch_searched_products(jsonData, "product-suggestion-table");
        }
    });
}
