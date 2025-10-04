from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/networkscanner/', include('networkscanner.urls')),
    path('api/webappscanner/', include('webappscanner.urls')),
    path("api/apiscanner/", include("apiscanner.urls")),
    path("api/sslscanner/", include("sslscanner.urls")),
    path("api/domainscanner/", include("domainscanner.urls")),
]
