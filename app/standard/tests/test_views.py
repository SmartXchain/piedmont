import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from standard.models import Standard


@pytest.mark.django_db
def test_standard_list_view(client):
    Standard.objects.create(name="Standard 1", description="Description 1", revision="Rev A", author="Author 1")
    Standard.objects.create(name="Standard 2", description="Description 2", revision="Rev B", author="Author 2")

    response = client.get(reverse('standard_list'))
    assert response.status_code == 200
    assert "Standard 1" in response.content.decode()
    assert "Standard 2" in response.content.decode()


@pytest.mark.django_db
def test_standard_detail_view(client):
    # Create a dummy file
    test_file = SimpleUploadedFile("test_file.pdf", b"file_content", content_type="application/pdf")

    # Create a dummy standard with the file
    standard = Standard.objects.create(
        name="Standard 1",
        description="Description 1",
        revision="Rev A",
        author="Author 1",
        upload_file=test_file,
    )

    response = client.get(reverse('standard_detail', args=[standard.id]))
    assert response.status_code == 200
    assert "Standard 1" in response.content.decode()
    assert "test_file.pdf" in response.content.decode()  # Verify file name appears in the response


@pytest.mark.django_db
def test_standard_create_view(client):
    test_file = SimpleUploadedFile("test_file.pdf", b"file_content", content_type="application/pdf")

    response = client.post(reverse('standard_create'), {
        "name": "New Standard",
        "description": "New Description",
        "revision": "Rev C",
        "author": "Author 3",
        "upload_file": test_file,
    })
    assert response.status_code == 302  # Redirect after success
    assert Standard.objects.count() == 1
    assert Standard.objects.first().name == "New Standard"
