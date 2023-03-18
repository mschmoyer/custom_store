$(document).ready(function() {

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
        $.ajax({
            type: "POST",
            url: "/buy/" + productId,
            data: JSON.stringify(shippingInfo),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (response) {
                // Hide the buyModal after a successful AJAX request
                $('#buyModal').modal('hide');
                document.querySelectorAll('.btn-buy').classList.remove('clicked');
            },
            error: function (error) {
                // Hide the buyModal after an unsuccessful AJAX request
                $('#buyModal').modal('hide');
                document.querySelectorAll('.btn-buy').classList.remove('clicked');
            },
        });
    });

    $('#buyModal').on('hidden.bs.modal', function() {
        // Remove the modal backdrop after the modal is hidden
        $('.modal-backdrop').remove();
    });
});