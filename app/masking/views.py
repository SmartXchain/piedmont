from django.shortcuts import render, get_object_or_404, redirect
from .models import MaskingProfile
from .forms import MaskingProfileForm
from django.db.models import F


def masking_profile_list(request):
    profiles = (
        MaskingProfile.objects
        .select_related('part_detail__part')  # Ensure related Part and PartDetail data is fetched
        .values(
            part_number=F('part_detail__part__part_number'),
            part_revision=F('part_detail__part__part_revision'),
            part_description=F('part_detail__part__part_description'),
        )
        .distinct()
    )
    return render(request, 'masking/masking_profile_list.html', {'profiles': profiles})



def masking_profile_detail(request, part_number, part_revision):
    profile = get_object_or_404(
        MaskingProfile,
        part_detail__part__part_number=part_number,
        part_detail__part__part_revision=part_revision
    )
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


def masking_detail_view(request, detail_id):
    detail = get_object_or_404(MaskingPhoto, id=detail_id)  # Replace `MaskingPhoto` with actual detail model
    return render(request, 'masking/masking_detail_view.html', {'detail': detail})



def masking_detail_add(request, profile_id):
    profile = get_object_or_404(MaskingProfile, id=profile_id)

    if request.method == "POST":
        form = MaskingProfileForm(request.POST)  # Replace with actual form for masking detail
        if form.is_valid():
            detail = form.save(commit=False)
            detail.profile = profile
            detail.save()
            return redirect('masking_profile_detail', part_number=profile.part.part_number, part_revision=profile.part.part_revision)
    else:
        form = MaskingProfileForm()  # Replace with actual form for masking detail

    return render(request, 'masking/masking_detail_form.html', {'form': form, 'profile': profile})


def masking_detail_edit(request, detail_id):
    detail = get_object_or_404(MaskingPhoto, id=detail_id)  # Replace `MaskingPhoto` with actual detail model

    if request.method == "POST":
        form = MaskingPhotoForm(request.POST, instance=detail)  # Replace `MaskingPhotoForm` with actual form
        if form.is_valid():
            form.save()
            return redirect('masking_profile_detail', part_number=detail.masking_profile.part.part_number, part_revision=detail.masking_profile.part.part_revision)
    else:
        form = MaskingPhotoForm(instance=detail)  # Replace `MaskingPhotoForm` with actual form

    return render(request, 'masking/masking_detail_form.html', {'form': form, 'detail': detail})


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

