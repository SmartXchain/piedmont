"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = "Piedmont Aviation"
admin.site.site_title = "CP"
admin.site.index_title = "Special Processes Admin Portal"


urlpatterns = [
    path('', include('landing_page.urls')),
    path('standard/', include('standard.urls')),
    path('part/', include('part.urls')),
    path('masking/', include('masking.urls')),
    path('inventory/', include('kanban.urls')),
    path('pm/', include('pm.urls')),
    path('fixtures/', include('fixtures.urls')),
    path('tanks/', include('tanks.urls')),
    path('process/', include('process.urls')),
    path('links/', include('customer_links.urls')),
    path('sds/', include('sds.urls')),
    path('admin/', admin.site.urls),
]
if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
