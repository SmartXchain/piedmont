from django.shortcuts import render, get_object_or_404, redirect
from .models import Method, ParameterToBeRecorded
from .forms import MethodForm, ParameterForm

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


def method_detail(request, method_id):
    method = get_object_or_404(Method, id=method_id)
    return render(request, 'methods/method_detail.html', {'method': method})




def parameter_list_view(request, method_id):
    method = get_object_or_404(Method, id=method_id)
    parameters = ParameterToBeRecorded.objects.filter(method=method)
    return render(request, 'methods/parameter_list.html', {'method': method, 'parameters': parameters})


def parameter_create_view(request, method_id):
    method = get_object_or_404(Method, id=method_id)
    print(f"Method ID: {method.id}, Method Title: {method.title}")
    if request.method == "POST":
        form = ParameterForm(request.POST)
        if form.is_valid():
            parameter = form.save(commit=False)
            parameter.method = method
            parameter.save()
            return redirect('parameter_list', method_id=method.id)
    else:
        form = ParameterForm()
    return render(request, 'methods/parameter_form.html', {'form': form, 'method': method})


def parameter_edit_view(request, method_id, parameter_id):
    method = get_object_or_404(Method, id=method_id)
    parameter = get_object_or_404(ParameterToBeRecorded, id=parameter_id, method=method)
    if request.method == "POST":
        form = ParameterForm(request.POST, instance=parameter)
        if form.is_valid():
            form.save()
            return redirect('parameter_list', method_id=method.id)
    else:
        form = ParameterForm(instance=parameter)
    return render(request, 'methods/parameter_form.html', {'form': form, 'method': method, 'parameter': parameter})
