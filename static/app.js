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

    // $('#successModal .modal-footer button').on('click', function() {
    //     $('#successModal').modal('hide');
    // });    

    // document.querySelectorAll('.btn-buy').forEach(btn => {
    //     btn.addEventListener('click', function(event) {
    //         event.preventDefault();
    //         //this.classList.add('clicked');
    //         $('#buyModal').modal('show');
    //     });
    // });

    // $('#buyModal').on('show.bs.modal', function (event) {
    //     var button = $(event.relatedTarget); // Button that triggered the modal
    //     var productId = button.data('product-id'); // Extract the product ID from data-* attributes
    //     $('#product-id').val(productId); // Update the hidden input field with the product ID
    // });

    function addToCart(productId) {
        // Send a POST request to the add_item_to_cart route with the product_id
        fetch('/add_item_to_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ product_id: productId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                // Show the "Item Added" modal
                $('#itemAddedModal').show();

                // Add event listener to "OK" button to hide modal when clicked
                const itemAddedModalOKButton = document.getElementById('itemAddedModalOKButton');
                itemAddedModalOKButton.addEventListener('click', () => {
                    $('#itemAddedModal').hide();
                });
            } else {
                // Handle errors (you can display a specific error message if needed)
                console.error('Error:', data.error);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
    

    document.querySelectorAll('.btn-add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            addToCart(productId);
        });
    });
    

    //document.getElementById('place-order-button').addEventListener('click', placeOrder);
    function placeOrder(shippingInfo) {
        // Show the loading indicator
        document.getElementById('loading-indicator').classList.remove('d-none');
    
        // Gather product_ids from the cart table
        const productIds = Array.from(document.querySelectorAll('tbody tr')).map(row => {
            return row.querySelector('td:nth-child(2)').textContent;
        });
    
        // Hide the buy modal
        $('#buyModal').modal('hide');

        // Send a POST request to the place_order route with the product_ids array and shippingInfo
        fetch('/place_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ product_ids: productIds, shipping_info: shippingInfo }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide the loading indicator
            document.getElementById('loading-indicator').classList.add('d-none');
            
            // Remove all the cart items from the page
            const cartItemRows = document.getElementsByClassName('cart_item_rows');
            while (cartItemRows.length > 0) {
                cartItemRows[0].remove();
            }

            if (data.message) {
                // Get a random thank you message
                const randomThankYouMessage = getRandomThankYouMessage();
    
                // Show the success message with the random thank you message
                const successMessageElement = document.getElementById('success-message');
                successMessageElement.textContent = randomThankYouMessage;
                successMessageElement.classList.remove('d-none');
            } else {
                // Handle errors (you can display a specific error message if needed)
                console.error('Error:', data.error);
            }
        })
        .catch((error) => {
            // Hide the loading indicator
            document.getElementById('loading-indicator').classList.add('d-none');
            console.error('Error:', error);
        });
    }
    
    
    
    document.getElementById('shipping-form').addEventListener('submit', function(event) {
        event.preventDefault();
    
        // Gather shipping information from the form
        const shippingInfo = {
            name: document.getElementById('name').value,
            street1: document.getElementById('street1').value,
            city: document.getElementById('city').value,
            state: document.getElementById('state').value,
            postalCode: document.getElementById('postalCode').value,
            country: document.getElementById('country').value,
        };
    
        // Call the placeOrder function with the shippingInfo
        placeOrder(shippingInfo);
    });
    

    // $('#shipping-form').on('submit', function(event) {
    //     event.preventDefault();
    //     var productId = $('#product-id').val();
    //     var shippingInfo = {
    //         name: $('#name').val(),
    //         street1: $('#street1').val(),
    //         city: $('#city').val(),
    //         state: $('#state').val(),
    //         postalCode: $('#postalCode').val(),
    //         country: $('#country').val()
    //     };
    //     // Show the successModal in the loading state
    //     $('#buyModal').modal('hide');
    //     $('#loadingMessage').show();
    //     $('#successMessage').hide();
    //     $('#successModal .modal-footer button').hide();
    //     $('#successModal').modal('show');

    //     $.ajax({
    //         type: "POST",
    //         url: "/buy/" + productId,
    //         data: JSON.stringify(shippingInfo),
    //         contentType: "application/json; charset=utf-8",
    //         dataType: "json",
    //         success: function (response) {
    //             // Update the successModal to show the success message
    //             $('#loadingMessage').hide();
    //             $('#successMessage').text(getRandomThankYouMessage()).show();
    //             $('#successModal .modal-footer button').show();
    //             document.querySelectorAll('.btn-buy').classList.remove('clicked');
    //         },
    //         error: function (error) {
    //             // Hide the successModal after an unsuccessful AJAX request
    //             $('#successModal').modal('hide');
    //             document.querySelectorAll('.btn-buy').classList.remove('clicked');
    //         },
    //     });
    // });
    
    

    $('#buyModal').on('hidden.bs.modal', function() {
        // Remove the modal backdrop after the modal is hidden
        $('.modal-backdrop').remove();
    });
});