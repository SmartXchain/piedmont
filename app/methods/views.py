from django.shortcuts import render, get_object_or_404, redirect
from .models import Method
from .forms import MethodForm


def method_list_view(request):
    methods = Method.objects.all()
    return render(request, 'methods/method_list.html', {'methods': methods})


def method_create_view(request):
    if request.method == "POST":
        form = MethodForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('method_list')
    else:
        form = MethodForm()
    return render(request, 'methods/method_form.html', {'form': form})


def method_edit_view(request, method_id):
    method = get_object_or_404(Method, id=method_id)
    if request.method == "POST":
        form = MethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            return redirect('method_list')
    else:
        form = MethodForm(instance=method)
    return render(request, 'methods/method_form.html', {'form': form, 'method': method})
