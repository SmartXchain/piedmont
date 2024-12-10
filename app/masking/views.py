from django.shortcuts import render, get_object_or_404, redirect
from .models import MaskingProfile, MaskingPhoto
from .forms import MaskingProfileForm, MaskingPhotoForm
from django.http import HttpResponse
from django.db.models import F


def masking_profile_list(request):
    profiles = MaskingProfile.objects.values(
        part_number=F('part__part_number'),
        part_revision=F('part__part_revision'),
        part_description=F('part__part_description'),
    ).distinct()
    return render(request, 'masking/masking_profile_list.html', {'profiles': profiles})


def masking_profile_detail(request, part_number, part_revision):
    profile = get_object_or_404(MaskingProfile, part__part_number=part_number, part__part_revision=part_revision)
    return render(request, 'masking/masking_profile_detail.html', {'profile': profile})


def masking_profile_edit(request, profile_id):
    profile = get_object_or_404(MaskingProfile, id=profile_id)

    if request.method == "POST":
        form = MaskingProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('masking_profile_list')
    else:
        form = MaskingProfileForm(instance=profile)

    return render(request, 'masking/masking_profile_form.html', {'form': form, 'profile': profile})

def masking_profile_create(request):
    if request.method == "POST":
        form = MaskingProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('masking_profile_list')
    else:
        form = MaskingProfileForm()

    return render(request, 'masking/masking_profile_form.html', {'form': form})



def masking_photo_create(request):
    masking_profile_id = request.GET.get('masking_profile')
    masking_profile = get_object_or_404(MaskingProfile, id=masking_profile_id)

    if request.method == "POST":
        form = MaskingPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.masking_profile = masking_profile
            photo.save()
            return redirect('masking_profile_detail', profile_id=masking_profile.id)
    else:
        form = MaskingPhotoForm()

    return render(request, 'masking/masking_photo_form.html', {'form': form, 'masking_profile': masking_profile})

