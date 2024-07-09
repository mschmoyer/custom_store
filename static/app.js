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

let simulationActive = false;
let simulationTimeout;

function showOrderNotification() {
    const notification = document.getElementById('order-notification');
    const button = document.getElementById('chaotic-order-button');

    const buttonRect = button.getBoundingClientRect();
    const offsetX = 100;
    const offsetY = -50;

    notification.style.left = `${buttonRect.left + offsetX}px`;
    notification.style.top = `${buttonRect.top + offsetY}px`;

    notification.classList.remove('d-none');
    notification.style.animation = 'floatUp 3s ease-out';

    setTimeout(() => {
        notification.classList.add('d-none');
    }, 3000);
}

function simulate_store() {
    if (!simulationActive) {
        return;
    }

    // Perform the POST request to the /submit_chaotic_order endpoint
    console.log('Simulating a customer order...');
    fetch('/submit_chaotic_order', { method: 'POST' })
        .then(response => {
            // Handle the response if necessary
            if (response.ok) {
                showOrderNotification();
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

    // Call simulate_store again after a random delay
    const randomDelay = Math.random() * 5000; // Random delay up to 5000 milliseconds (5 seconds)
    simulationTimeout = setTimeout(simulate_store, randomDelay);
}

function start_simulation() {
    simulationActive = true;
    simulate_store();
}

function stop_simulation() {
    simulationActive = false;
    clearTimeout(simulationTimeout);
}


$(document).ready(function() {

    $("#search-input").on("keyup", function () {
        filterProducts();
    });

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
                setTimeout(() => {
                    $('#itemAddedModal').hide();
                },1500);
            } else {
                // Handle errors (you can display a specific error message if needed)
                console.error('Error:', data.error);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
    
    let isSimulationRunning = false;

    document.getElementById('chaotic-order-button').addEventListener('click', function() {
        if (isSimulationRunning) {
            stop_simulation();
            this.textContent = 'Simulate Business';
        } else {
            start_simulation();
            this.textContent = 'Stop Simulating';
        }

        isSimulationRunning = !isSimulationRunning;
    });

    
    document.querySelectorAll('.btn-add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            addToCart(productId);
        });
    });

    document.querySelectorAll('.btn-buy-now').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            addToCart(productId);
            placeOrder()
        });
    });
    
    document.getElementById('place-order-button').addEventListener('click', function() {
        placeOrder();
    });

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
        fetch('/place_order_db', {
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
    
    if (document.getElementById('shipping-form')) {
        document.getElementById('shipping-form').addEventListener('submit', function(event) {
            event.preventDefault();
        
            // Gather shipping information from the form
            const shippingInfo = {
                Name: document.getElementById('name').value,
                Address1: document.getElementById('street1').value,
                City: document.getElementById('city').value,
                State: document.getElementById('state').value,
                PostalCode: document.getElementById('postalCode').value,
                //Country: document.getElementById('country').value,
                Country: 'US',
            };
        
            // Call the placeOrder function with the shippingInfo
            placeOrder(shippingInfo);
        });   
    }

    $('#buyModal').on('hidden.bs.modal', function() {
        // Remove the modal backdrop after the modal is hidden
        $('.modal-backdrop').remove();
    });

    $('#buyModal').on('shown.bs.modal', function() {
        // Load the address data from local storage
        var address = JSON.parse(localStorage.getItem('address'));

        // If there's address data in local storage...
        if (address) {
            // Set the values of the form fields
            $('#name').val(address.full_name || '');
            $('#street1').val(address.ln1 || '');
            $('#city').val(address.city || '');
            $('#state').val(address.state || '');
            $('#postalCode').val(address.zip || '');
            $('#country').val(address.country || '');
        }
    });


});