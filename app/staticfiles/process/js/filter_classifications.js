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

(function($) {
    $(document).ready(function() {
        function updateMethodOverview(methodId) {
            if (!methodId) {
                $('#method-overview').html('');
                return;
            }

            $.ajax({
                url: '/admin/process/get_method_info/',
                data: { method_id: methodId },
                success: function(data) {
                    $('#method-overview').html(
                        `<div style="border:1px solid #ccc; padding:10px; margin-top:10px;">
                            <strong>${data.title}</strong> (${data.method_type})<br>
                            <em>${data.description || 'No description'}</em><br>
                            ${data.tank_name ? `<strong>Tank:</strong> ${data.tank_name}<br>` : ''}
                            ${data.chemical ? `<strong>Chemical:</strong> ${data.chemical}<br>` : ''}
                            ${data.is_rectified ? `<strong>Rectified</strong>` : ''}
                        </div>`
                    );
                },
                error: function() {
                    $('#method-overview').html('<div style="color:red;">Error loading method info.</div>');
                }
            });
        }

        $(document).on('change', 'select[name$="method"]', function() {
            const methodId = $(this).val();
            updateMethodOverview(methodId);
        });

        // Trigger on load (if editing)
        $('select[name$="method"]').each(function() {
            const methodId = $(this).val();
            if (methodId) {
                updateMethodOverview(methodId);
            }
        });
    });
})(django.jQuery);
