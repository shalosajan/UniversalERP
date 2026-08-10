from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(
        max_length=50, unique=True, help_text="Internal Stock Keeping Unit"
    )
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    hsn_code = models.CharField(max_length=20, default="61")

    # Pricing
    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Maximum Retail Price (Inclusive of Tax)",
    )
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price before tax"
    )

    # Stock
    current_stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"
