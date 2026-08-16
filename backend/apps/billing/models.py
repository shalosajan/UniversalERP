from django.contrib.auth.models import User
from django.db import models

from apps.inventory.models import Product


class Customer(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    state = models.CharField(max_length=50, default="Kerala")

    def __str__(self):
        return self.name if self.name else self.phone


class Invoice(models.Model):
    PAYMENT_CHOICES = [
        ("CASH", "Cash"),
        ("UPI", "UPI"),
        ("CARD", "Card"),
    ]
    STATUS_CHOICES = [
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    cashier = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="sales_handled", null=True
    )

    # Retail Additions
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_CHOICES, default="CASH"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="PAID")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Tax Totals
    taxable_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cgst_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sgst_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    igst_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.invoice_number} - {self.status}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Snapshot Fields
    item_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Exclusive of tax"
    )

    # Tax tracking
    gst_rate_applied = models.DecimalField(max_digits=5, decimal_places=2)
    item_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.item_name} (Inv: {self.invoice.invoice_number})"
