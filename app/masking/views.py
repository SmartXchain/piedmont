from django.shortcuts import render, get_object_or_404, redirect
from .models import MaskingProfile, MaskingPhoto
from .forms import MaskingProfileForm, MaskingPhotoForm
from django.http import HttpResponse


def masking_profile_list(request):
    profiles = MaskingProfile.objects.all()
    return render(request, 'masking/masking_profile_list.html', {'profiles': profiles})


def masking_profile_detail(request, profile_id):
    profile = get_object_or_404(MaskingProfile, id=profile_id)
    photos = profile.photos.all()
    return render(request, 'masking/masking_profile_detail.html', {'profile': profile, 'photos': photos})


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
    masking_profile_id = request.GET.get('masking_profile')  # Retrieve from query params
    if not masking_profile_id:
        return HttpResponse("Masking Profile ID is missing.", status=400)  # Handle missing ID gracefully

    masking_profile = get_object_or_404(MaskingProfile, id=masking_profile_id)

    if request.method == "POST":
        form = MaskingPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.masking_profile = masking_profile  # Associate with the correct masking profile
            photo.save()
            return redirect('masking_profile_detail', profile_id=masking_profile.id)
    else:
        form = MaskingPhotoForm()

    return render(request, 'masking/masking_photo_form.html', {
        'form': form,
        'masking_profile': masking_profile,
    })
