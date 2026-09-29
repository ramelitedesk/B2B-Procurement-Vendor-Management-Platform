from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.shortcuts import render

from vendors.models import Vendor, VendorPerformanceHistory
from products.models import Product
from purchase_orders.models import PurchaseOrder, PurchaseOrderItem
from deliveries.models import Delivery
from invoices.models import Invoice
from payments.models import Payment


@login_required
def reports_dashboard(request):

    user = request.user
    company = user.company

    # ---------------------------------------------------------
    # BASE QUERYSETS
    # ---------------------------------------------------------

    if user.role == "SUPER_ADMIN":

        vendors = Vendor.objects.all()
        products = Product.objects.all()
        purchase_orders = PurchaseOrder.objects.all()
        deliveries = Delivery.objects.all()
        invoices = Invoice.objects.all()
        payments = Payment.objects.all()
        performance_history = VendorPerformanceHistory.objects.all()
        po_items = PurchaseOrderItem.objects.all()

    else:

        if not company:
            return render(
                request,
                "reports/reports_dashboard.html",
                {
                    "user": user,
                    "company": None,
                    "error_message": (
                        "Your user account is not assigned to a company."
                    ),
                },
            )

        vendors = Vendor.objects.filter(company=company)

        products = Product.objects.filter(
            company=company
        )

        purchase_orders = PurchaseOrder.objects.filter(
            company=company
        )

        deliveries = Delivery.objects.filter(
            purchase_order__company=company
        )

        invoices = Invoice.objects.filter(
            purchase_order__company=company
        )

        payments = Payment.objects.filter(
            company=company
        )

        performance_history = VendorPerformanceHistory.objects.filter(
            vendor__company=company
        )

        po_items = PurchaseOrderItem.objects.filter(
            purchase_order__company=company
        )

    # ---------------------------------------------------------
    # PURCHASE SPEND
    # ---------------------------------------------------------

    purchase_spend = (
        purchase_orders
        .exclude(
            status=PurchaseOrder.Status.CANCELLED
        )
        .aggregate(
            total=Sum("total_amount")
        )
        .get("total")
        or Decimal("0.00")
    )

    # ---------------------------------------------------------
    # TOTAL PAID
    # ---------------------------------------------------------

    total_paid = (
        payments
        .exclude(
            status=Payment.Status.CANCELLED
        )
        .aggregate(
            total=Sum("amount")
        )
        .get("total")
        or Decimal("0.00")
    )

    # ---------------------------------------------------------
    # OUTSTANDING
    # ---------------------------------------------------------

    outstanding_amount = purchase_spend - total_paid

    # Prevent negative display if payments exceed purchase spend.
    if outstanding_amount < Decimal("0.00"):
        outstanding_amount = Decimal("0.00")

    # ---------------------------------------------------------
    # PURCHASE ORDER SUMMARY
    # ---------------------------------------------------------

    purchase_order_summary = {
        "total": purchase_orders.count(),

        "draft": purchase_orders.filter(
            status=PurchaseOrder.Status.DRAFT
        ).count(),

        "sent": purchase_orders.filter(
            status=PurchaseOrder.Status.SENT
        ).count(),

        "acknowledged": purchase_orders.filter(
            status=PurchaseOrder.Status.ACKNOWLEDGED
        ).count(),

        "partially_delivered": purchase_orders.filter(
            status=PurchaseOrder.Status.PARTIALLY_DELIVERED
        ).count(),

        "delivered": purchase_orders.filter(
            status=PurchaseOrder.Status.DELIVERED
        ).count(),

        "cancelled": purchase_orders.filter(
            status=PurchaseOrder.Status.CANCELLED
        ).count(),

        "closed": purchase_orders.filter(
            status=PurchaseOrder.Status.CLOSED
        ).count(),
    }

    # ---------------------------------------------------------
    # VENDOR SUMMARY
    # ---------------------------------------------------------

    vendor_summary = []

    for vendor in vendors.order_by("name"):

        vendor_orders = purchase_orders.filter(
            vendor=vendor
        )

        order_value = (
            vendor_orders
            .exclude(
                status=PurchaseOrder.Status.CANCELLED
            )
            .aggregate(
                total=Sum("total_amount")
            )
            .get("total")
            or Decimal("0.00")
        )

        vendor_summary.append({
            "vendor": vendor,
            "order_count": vendor_orders.count(),
            "order_value": order_value,
        })

    # ---------------------------------------------------------
    # VENDOR PERFORMANCE
    # ---------------------------------------------------------

    vendor_performance = (
        performance_history
        .values(
            "vendor_id",
            "vendor__name",
        )
        .annotate(
            evaluation_count=Count("id"),
            average_delivery=Avg("delivery_score"),
            average_quality=Avg("quality_score"),
            average_pricing=Avg("pricing_score"),
            average_service=Avg("service_score"),
            average_overall=Avg("overall_score"),
        )
        .order_by("-average_overall")
    )

    # ---------------------------------------------------------
    # DELIVERY PERFORMANCE
    # ---------------------------------------------------------

    delivery_summary = {
        "total": deliveries.count(),

        "draft": deliveries.filter(
            status=Delivery.Status.DRAFT
        ).count(),

        "in_transit": deliveries.filter(
            status=Delivery.Status.IN_TRANSIT
        ).count(),

        "partially_delivered": deliveries.filter(
            status=Delivery.Status.PARTIALLY_DELIVERED
        ).count(),

        "delivered": deliveries.filter(
            status=Delivery.Status.DELIVERED
        ).count(),

        "cancelled": deliveries.filter(
            status=Delivery.Status.CANCELLED
        ).count(),
    }

    # ---------------------------------------------------------
    # INVOICE SUMMARY
    # ---------------------------------------------------------

    invoice_summary = {
        "total": invoices.count(),

        "uploaded": invoices.filter(
            status=Invoice.Status.UPLOADED
        ).count(),

        "under_review": invoices.filter(
            status=Invoice.Status.UNDER_REVIEW
        ).count(),

        "approved": invoices.filter(
            status=Invoice.Status.APPROVED
        ).count(),

        "rejected": invoices.filter(
            status=Invoice.Status.REJECTED
        ).count(),

        "paid": invoices.filter(
            status=Invoice.Status.PAID
        ).count(),
    }

    # ---------------------------------------------------------
    # CATEGORY-WISE SPEND
    # ---------------------------------------------------------

    category_spend = (
        po_items
        .exclude(
            purchase_order__status=PurchaseOrder.Status.CANCELLED
        )
        .values(
            "product__category__id",
            "product__category__name",
        )
        .annotate(
            total_spend=Sum("total_amount"),
            total_quantity=Sum("quantity"),
            order_count=Count(
                "purchase_order",
                distinct=True
            ),
        )
        .order_by("-total_spend")
    )

    # ---------------------------------------------------------
    # RECENT PURCHASE ORDERS
    # ---------------------------------------------------------

    recent_purchase_orders = (
        purchase_orders
        .select_related("vendor")
        .order_by("-created_at")[:10]
    )

    # ---------------------------------------------------------
    # RECENT INVOICES
    # ---------------------------------------------------------

    recent_invoices = (
        invoices
        .select_related(
            "vendor",
            "purchase_order"
        )
        .order_by("-created_at")[:10]
    )

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------

    context = {
        "user": user,
        "company": company,

        "purchase_spend": purchase_spend,
        "total_paid": total_paid,
        "outstanding_amount": outstanding_amount,

        "vendor_count": vendors.count(),
        "product_count": products.count(),

        "purchase_order_summary": purchase_order_summary,

        "vendor_summary": vendor_summary,

        "vendor_performance": vendor_performance,

        "delivery_summary": delivery_summary,

        "invoice_summary": invoice_summary,

        "category_spend": category_spend,

        "recent_purchase_orders": recent_purchase_orders,

        "recent_invoices": recent_invoices,
    }

    return render(
        request,
        "reports/reports_dashboard.html",
        context
    )