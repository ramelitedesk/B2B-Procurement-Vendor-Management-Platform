from django.urls import path
from .views import vendor_list

app_name = "vendors"

urlpatterns = [
    path("", vendor_list, name="list"),
]