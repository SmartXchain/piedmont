# process/views.py
from django.http import JsonResponse
from standard.models import Classification
from methods.models import Method


def get_classifications(request):
    standard_id = request.GET.get('standard_id')
    if not standard_id:
        return JsonResponse([], safe=False)

    classifications = Classification.objects.filter(standard_id=standard_id)
    data = [{'id': c.id, 'text': str(c)} for c in classifications]
    return JsonResponse(data, safe=False)


def get_method_info(request):
    method_id = request.GET.get('method_id')
    if not method_id:
        return JsonResponse({'error': 'No method ID provided'}, status=400)

    try:
        method = Method.objects.get(id=method_id)
        return JsonResponse({
            'title': method.title,
            'description': method.description,
            'method_type': method.method_type,
            'chemical': method.chemical,
            'tank_name': method.tank_name,
            'is_rectified': method.is_rectified,
            'is_strike_etch': method.is_strike_etch,
        })
    except Method.DoesNotExist:
        return JsonResponse({'error': 'Method not found'}, status=404)
