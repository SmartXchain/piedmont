// filter_classifications.js
(function($) {
    $(document).ready(function() {
        $('#id_standard').change(function() {
            const standardId = $(this).val();
            const classificationSelect = $('#id_classification');

            if (!standardId) {
                classificationSelect.empty().append('<option value="">---------</option>');
                return;
            }

            $.ajax({
                url: `/admin/process/get_classifications/`,
                data: {
                    standard_id: standardId
                },
                success: function(data) {
                    classificationSelect.empty().append('<option value="">---------</option>');
                    data.forEach(function(item) {
                        classificationSelect.append(
                            $('<option>', { value: item.id, text: item.text })
                        );
                    });
                },
                error: function() {
                    console.error("Failed to load classifications.");
                }
            });
        });
    });
})(django.jQuery);
