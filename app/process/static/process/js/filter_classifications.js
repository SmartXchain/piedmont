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


// static/process/js/filter_classifications.js
(function($) {
    $(document).ready(function() {
        const standardSelect = $('#id_standard');
        const classificationSelect = $('#id_classification');

        function loadClassifications(standardId) {
            classificationSelect.empty().append('<option value="">---------</option>');

            if (!standardId) return;

            $.ajax({
                url: '/admin/process/get_classifications/',
                data: { standard_id: standardId },
                success: function(data) {
                    data.forEach(item => {
                        classificationSelect.append(
                            $('<option>', { value: item.id, text: item.text })
                        );
                    });
                },
                error: function() {
                    console.error("Failed to load classifications.");
                }
            });
        }

        // Trigger on change
        standardSelect.change(function() {
            loadClassifications($(this).val());
        });

        // Trigger on load (for edit mode)
        if (standardSelect.val()) {
            loadClassifications(standardSelect.val());
        }
    });
})(django.jQuery);
