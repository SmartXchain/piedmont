(function($) {
    $(document).ready(function() {
        const $standard = $('#id_standard');
        const $classification = $('#id_classification');

        function loadClassifications(standardId, selectedId = null) {
            $classification.empty().append('<option value="">---------</option>');
            if (!standardId) return;

            $.ajax({
                url: '/admin/process/get_classifications/',
                data: { standard_id: standardId },
                success: function(data) {
                    data.forEach(item => {
                        const option = $('<option>', {
                            value: item.id,
                            text: item.text
                        });
                        if (selectedId && item.id == selectedId) {
                            option.prop('selected', true);
                        }
                        $classification.append(option);
                    });
                },
                error: function() {
                    console.error("Failed to load classifications.");
                }
            });
        }

        $standard.change(function() {
            loadClassifications($(this).val());
        });

        if ($standard.val()) {
            loadClassifications($standard.val(), $classification.val());
        }
    });
})(django.jQuery);
