from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from vendors.models import Vendor
from products.models import Product
from procurement.models import PurchaseRequisition
from rfq.models import RFQ
from quotations.models import Quotation
from purchase_orders.models import PurchaseOrder
from deliveries.models import Delivery
from invoices.models import Invoice
from payments.models import Payment


@login_required
def dashboard(request):

    user = request.user
    company = user.company

    context = {
        "user": user,
        "company": company,
    }

    # ---------------------------------------------------------
    # SUPER ADMIN
    # ---------------------------------------------------------
    if user.role == "SUPER_ADMIN":

        context.update({
            "vendor_count": Vendor.objects.count(),
            "product_count": Product.objects.count(),
            "requisition_count": PurchaseRequisition.objects.count(),
            "rfq_count": RFQ.objects.count(),
            "quotation_count": Quotation.objects.count(),
            "purchase_order_count": PurchaseOrder.objects.count(),
            "delivery_count": Delivery.objects.count(),
            "invoice_count": Invoice.objects.count(),
            "payment_count": Payment.objects.count(),
        })

        return render(
            request,
            "dashboard/super_admin_dashboard.html",
            context
        )

    # ---------------------------------------------------------
    # COMPANY ADMIN
    # ---------------------------------------------------------
    if user.role == "COMPANY_ADMIN":

        vendors = Vendor.objects.filter(company=company)
        products = Product.objects.filter(company=company)
        requisitions = PurchaseRequisition.objects.filter(company=company)
        rfqs = RFQ.objects.filter(company=company)
        purchase_orders = PurchaseOrder.objects.filter(company=company)
        deliveries = Delivery.objects.filter(
            purchase_order__company=company
        )
        invoices = Invoice.objects.filter(
            purchase_order__company=company
        )
        payments = Payment.objects.filter(company=company)

        total_purchase_value = (
            purchase_orders
            .exclude(status=PurchaseOrder.Status.CANCELLED)
            .aggregate(total=Sum("total"))
            .get("total")
            or 0
        )

        total_paid = (
            payments
            .exclude(status=Payment.Status.CANCELLED)
            .aggregate(total=Sum("amount"))
            .get("total")
            or 0
        )

        context.update({
            "vendor_count": vendors.count(),
            "product_count": products.count(),
            "requisition_count": requisitions.count(),
            "pending_requisition_count": requisitions.filter(
                status=PurchaseRequisition.Status.PENDING_APPROVAL
            ).count(),
            "rfq_count": rfqs.count(),
            "purchase_order_count": purchase_orders.count(),
            "delivery_count": deliveries.count(),
            "invoice_count": invoices.count(),
            "payment_count": payments.count(),
            "total_purchase_value": total_purchase_value,
            "total_paid": total_paid,
        })

        return render(
            request,
            "dashboard/company_admin_dashboard.html",
            context
        )

    # ---------------------------------------------------------
    # PROCUREMENT MANAGER
    # ---------------------------------------------------------
    if user.role == "PROCUREMENT_MANAGER":

        requisitions = PurchaseRequisition.objects.filter(
            company=company
        )

        rfqs = RFQ.objects.filter(company=company)

        quotations = Quotation.objects.filter(
            rfq__company=company
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

        context.update({
            "pending_requisition_count": requisitions.filter(
                status=PurchaseRequisition.Status.PENDING_APPROVAL
            ).count(),

            "approved_requisition_count": requisitions.filter(
                status=PurchaseRequisition.Status.APPROVED
            ).count(),

            "rfq_count": rfqs.count(),

            "published_rfq_count": rfqs.filter(
                status=RFQ.Status.PUBLISHED
            ).count(),

            "quotation_count": quotations.count(),

            "submitted_quotation_count": quotations.filter(
                status=Quotation.Status.SUBMITTED
            ).count(),

            "purchase_order_count": purchase_orders.count(),

            "acknowledged_po_count": purchase_orders.filter(
                status=PurchaseOrder.Status.ACKNOWLEDGED
            ).count(),

            "delivery_count": deliveries.count(),

            "invoice_count": invoices.count(),
        })

        return render(
            request,
            "dashboard/procurement_manager_dashboard.html",
            context
        )

    # ---------------------------------------------------------
    # EMPLOYEE
    # ---------------------------------------------------------
    if user.role == "EMPLOYEE":

        requisitions = PurchaseRequisition.objects.filter(
            company=company,
            requested_by=user
        )

        context.update({
            "requisition_count": requisitions.count(),

            "draft_count": requisitions.filter(
                status=PurchaseRequisition.Status.DRAFT
            ).count(),

            "pending_count": requisitions.filter(
                status=PurchaseRequisition.Status.PENDING_APPROVAL
            ).count(),

            "approved_count": requisitions.filter(
                status=PurchaseRequisition.Status.APPROVED
            ).count(),

            "rejected_count": requisitions.filter(
                status=PurchaseRequisition.Status.REJECTED
            ).count(),
        })

        return render(
            request,
            "dashboard/employee_dashboard.html",
            context
        )

    # ---------------------------------------------------------
    # VENDOR
    # ---------------------------------------------------------
    if user.role == "VENDOR":

        # Current data model associates users with Company,
        # while Vendor is a separate company-level entity.
        # Therefore we currently show vendor-company level data.

        vendor_count = Vendor.objects.filter(
            company=company
        ).count()

        quotation_count = Quotation.objects.filter(
            vendor__company=company
        ).count()

        submitted_quotation_count = Quotation.objects.filter(
            vendor__company=company,
            status=Quotation.Status.SUBMITTED
        ).count()

        accepted_quotation_count = Quotation.objects.filter(
            vendor__company=company,
            status=Quotation.Status.ACCEPTED
        ).count()

        purchase_order_count = PurchaseOrder.objects.filter(
            vendor__company=company
        ).count()

        delivery_count = Delivery.objects.filter(
            vendor__company=company
        ).count()

        invoice_count = Invoice.objects.filter(
            vendor__company=company
        ).count()

        context.update({
            "vendor_count": vendor_count,
            "quotation_count": quotation_count,
            "submitted_quotation_count": submitted_quotation_count,
            "accepted_quotation_count": accepted_quotation_count,
            "purchase_order_count": purchase_order_count,
            "delivery_count": delivery_count,
            "invoice_count": invoice_count,
        })

        return render(
            request,
            "dashboard/vendor_dashboard.html",
            context
        )

    # ---------------------------------------------------------
    # DEFAULT
    # ---------------------------------------------------------

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )