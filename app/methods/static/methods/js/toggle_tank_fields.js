(function($) {
    $(document).ready(function() {
        function toggleTankFields() {
            var selected = $('#id_method_type').val();
            var tankSection = $('.tank-details-section');

            if (selected === 'processing_tank') {
                tankSection.removeClass('collapse').show();
            } else {
                tankSection.addClass('collapse').hide();
            }
        }

        toggleTankFields();  // Run on page load

        $('#id_method_type').change(function() {
            toggleTankFields();
        });
    });
})(django.jQuery);
