from django.db import models
from companies.models import Company


class Vendor(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"
        BLACKLISTED = "BLACKLISTED", "Blacklisted"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="vendors",
    )

    name = models.CharField(
        max_length=255
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    gst_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    address = models.TextField(
        blank=True,
        null=True,
    )

    website = models.URLField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class VendorContact(models.Model):

    class ContactType(models.TextChoices):
        PRIMARY = "PRIMARY", "Primary"
        SALES = "SALES", "Sales"
        ACCOUNTS = "ACCOUNTS", "Accounts"
        SUPPORT = "SUPPORT", "Support"
        OTHER = "OTHER", "Other"

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    name = models.CharField(
        max_length=255
    )

    designation = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )

    email = models.EmailField(
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    contact_type = models.CharField(
        max_length=20,
        choices=ContactType.choices,
        default=ContactType.OTHER,
    )

    is_primary = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.name} - {self.vendor.name}"

class VendorBankDetails(models.Model):

    class AccountType(models.TextChoices):
        SAVINGS = "SAVINGS", "Savings"
        CURRENT = "CURRENT", "Current"
        OTHER = "OTHER", "Other"

    vendor = models.OneToOneField(
        Vendor,
        on_delete=models.CASCADE,
        related_name="bank_details",
    )

    bank_name = models.CharField(
        max_length=255
    )

    account_holder_name = models.CharField(
        max_length=255
    )

    account_number = models.CharField(
        max_length=100
    )

    ifsc_code = models.CharField(
        max_length=20,
    )

    branch_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.CURRENT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.vendor.name} - {self.bank_name}"    

class VendorDocument(models.Model):

    class DocumentType(models.TextChoices):
        GST_CERTIFICATE = "GST_CERTIFICATE", "GST Certificate"
        PAN_CARD = "PAN_CARD", "PAN Card"
        REGISTRATION_CERTIFICATE = "REGISTRATION_CERTIFICATE", "Registration Certificate"
        MSME_CERTIFICATE = "MSME_CERTIFICATE", "MSME Certificate"
        BANK_PROOF = "BANK_PROOF", "Bank Proof"
        AGREEMENT = "AGREEMENT", "Agreement"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )

    title = models.CharField(max_length=255)

    file = models.FileField(
        upload_to="vendor_documents/",
    )

    document_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    issue_date = models.DateField(
        blank=True,
        null=True,
    )

    expiry_date = models.DateField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vendor.name} - {self.title}"    
    

class VendorPerformanceHistory(models.Model):

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="performance_history",
    )

    evaluation_date = models.DateField()

    delivery_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
    )

    quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
    )

    pricing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
    )

    service_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
    )

    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
    )

    comments = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.vendor.name} - {self.evaluation_date}"    