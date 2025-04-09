# process/views.py
from django.http import JsonResponse
from standard.models import Classification


def get_classifications(request):
    standard_id = request.GET.get('standard_id')
    data = []

    if standard_id:
        classifications = Classification.objects.filter(standard_id=standard_id)
        data = [{'id': c.id, 'text': str(c)} for c in classifications]

    return JsonResponse(data, safe=False)
