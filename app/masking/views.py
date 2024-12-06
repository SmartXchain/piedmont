from django.shortcuts import render, get_object_or_404, redirect
from .models import MaskingProfile, MaskingPhoto
from .forms import MaskingProfileForm, MaskingPhotoForm
from django.http import HttpResponse


def masking_profile_list(request):
    profiles = MaskingProfile.objects.all()
    return render(request, 'masking/masking_profile_list.html', {'profiles': profiles})


def masking_profile_detail(request, profile_id):
    profile = get_object_or_404(MaskingProfile, id=profile_id)
    related_profiles = MaskingProfile.objects.filter(part=profile.part).exclude(id=profile.id)
    return render(request, 'masking/masking_profile_detail.html', {
        'profile': profile,
        'related_profiles': related_profiles,
    })

def masking_profile_create(request):
    if request.method == "POST":
        print("POST data received:", request.POST)  # Debugging
        form = MaskingProfileForm(request.POST)
        if form.is_valid():
            print("Form is valid.")  # Debugging
            form.save()
            return redirect('masking_profile_list')
        else:
            print("Form errors:", form.errors)  # Debugging
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

