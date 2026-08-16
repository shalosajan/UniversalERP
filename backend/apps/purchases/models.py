from django.db import models

from apps.inventory.models import Product


class Vendor(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    state = models.CharField(max_length=50, default="Kerala")

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name="purchase_orders"
    )
    order_date = models.DateField(auto_now_add=True)
    invoice_number = models.CharField(
        max_length=100, help_text="Invoice number provided by the vendor"
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"PO-{self.id} | {self.vendor.name}"

    # Add this inside the PurchaseOrder class


STATUS_CHOICES = [
    ("DRAFT", "Draft"),
    ("PLACED", "Placed"),
    ("RECEIVED", "Received"),
    ("CANCELLED", "Cancelled"),
]
status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="DRAFT")


class PurchaseItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
