from django.urls import path

from .views import reports_dashboard


app_name = "reports"


urlpatterns = [
    path("", reports_dashboard, name="dashboard"),
]