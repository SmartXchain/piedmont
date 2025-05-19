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
                dataType: 'json',
                success: function(data) {
                    for (let i = 0; i < data.length; i++) {
                        let option = $('<option>', {
                            value: data[i].id,
                            text: data[i].text
                        });
                        if (selectedId && data[i].id == selectedId) {
                            option.prop('selected', true);
                        }
                        $classification.append(option);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Classification AJAX error:", error);
                }
            });
        }

        $standard.on('change', function() {
            loadClassifications($(this).val());
        });

        if ($standard.val()) {
            loadClassifications($standard.val(), $classification.val());
        }
    });
})(django.jQuery);
