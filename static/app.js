function filterProducts() {
    var input = document.getElementById("search-input");
    var filter = input.value.toUpperCase();
    var productContainers = document.getElementsByClassName("product-container");

    for (var i = 0; i < productContainers.length; i++) {
        var productName = productContainers[i].querySelector(".card-title");
        productContainers[i].classList.remove("fade-in");
        
        if (productName.innerHTML.toUpperCase().indexOf(filter) > -1) {
            productContainers[i].style.display = "";
        } else {
            productContainers[i].style.display = "none";
        }
    }
}

function getRandomThankYouMessage() {
    const messages = [
        "🎉 Thank you for your purchase! Your order is on its way! 🚀",
        "🥳 Woohoo! Thanks for buying from us! Your package will arrive soon! 📦",
        "🤩 You're awesome! Thanks for your order! We're preparing it right now! 🛍️",
        "🙌 You just made our day! Thank you for your purchase! 🌟",
        "💥 Boom! Your order has been received! Thanks for shopping with us! 🛒",
        "🏆 Thanks for being a champion shopper! Your order is being processed! 🎖️",
        "🕺💃 You've got great taste! Thanks for your order! It's on its way! 🚚",
        "🎁 Yay! We're so excited to send you your order! Thanks for buying! 💌",
        "🚀 You're out of this world! Thanks for your purchase! Your order is on its way! 🌠",
        "👏 High five! Thanks for your order! We're getting it ready for you! 📬"
    ];

    const randomIndex = Math.floor(Math.random() * messages.length);
    return messages[randomIndex];
}

$(document).ready(function() {

    $("#search-input").on("keyup", function () {
        filterProducts();
    });

    $('#successModal .modal-footer button').on('click', function() {
        $('#successModal').modal('hide');
    });    

    document.querySelectorAll('.btn-buy').forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.preventDefault();
            //this.classList.add('clicked');
            $('#buyModal').modal('show');
        });
    });

    $('#buyModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget); // Button that triggered the modal
        var productId = button.data('product-id'); // Extract the product ID from data-* attributes
        $('#product-id').val(productId); // Update the hidden input field with the product ID
    });

    $('#shipping-form').on('submit', function(event) {
        event.preventDefault();
        var productId = $('#product-id').val();
        var shippingInfo = {
            name: $('#name').val(),
            street1: $('#street1').val(),
            city: $('#city').val(),
            state: $('#state').val(),
            postalCode: $('#postalCode').val(),
            country: $('#country').val()
        };
        // Show the successModal in the loading state
        $('#buyModal').modal('hide');
        $('#loadingMessage').show();
        $('#successMessage').hide();
        $('#successModal .modal-footer button').hide();
        $('#successModal').modal('show');

        $.ajax({
            type: "POST",
            url: "/buy/" + productId,
            data: JSON.stringify(shippingInfo),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (response) {
                // Update the successModal to show the success message
                $('#loadingMessage').hide();
                $('#successMessage').text(getRandomThankYouMessage()).show();
                $('#successModal .modal-footer button').show();
                document.querySelectorAll('.btn-buy').classList.remove('clicked');
            },
            error: function (error) {
                // Hide the successModal after an unsuccessful AJAX request
                $('#successModal').modal('hide');
                document.querySelectorAll('.btn-buy').classList.remove('clicked');
            },
        });
    });
    
    

    $('#buyModal').on('hidden.bs.modal', function() {
        // Remove the modal backdrop after the modal is hidden
        $('.modal-backdrop').remove();
    });
});