from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Vendor


@login_required
def vendor_list(request):
    vendors = Vendor.objects.all().order_by("-created_at")

    context = {
        "vendors": vendors,
        "vendor_count": vendors.count(),
    }

    return render(
        request,
        "vendors/vendor_list.html",
        context,
    )