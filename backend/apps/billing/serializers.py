from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import Customer, Invoice, InvoiceItem


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class InvoiceItemSerializer(serializers.ModelSerializer):
    # These are calculated by the backend, so the frontend isn't allowed to write them
    item_name = serializers.CharField(read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    gst_rate_applied = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    item_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = InvoiceItem
        fields = [
            "product",
            "quantity",
            "item_name",
            "unit_price",
            "gst_rate_applied",
            "item_total",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    # Protect totals from being spoofed by the frontend
    taxable_value = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    cgst_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    sgst_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    igst_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    grand_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Invoice
        fields = "__all__"

    def validate(self, data):
        """
        Enterprise Guardrail: Prevent selling stock we don't have.
        """
        items_data = data.get("items", [])
        for item_data in items_data:
            product = item_data["product"]
            requested_qty = item_data["quantity"]

            if product.current_stock < requested_qty:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}. Available: {product.current_stock}, Requested: {requested_qty}"
                )
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")

        # State Routing: Default to Kerala for walk-ins
        customer = validated_data.get("customer")
        customer_state = (
            customer.state.lower() if customer and customer.state else "kerala"
        )
        is_interstate = customer_state != "kerala"

        invoice = Invoice.objects.create(**validated_data)

        taxable_value_total = Decimal("0.00")
        cgst_sum = Decimal("0.00")
        sgst_sum = Decimal("0.00")
        igst_sum = Decimal("0.00")

        for item_data in items_data:
            product = item_data["product"]
            qty = item_data["quantity"]

            # Dynamic GST Garment Rule: <= 1000 is 5%, otherwise 18%
            gst_rate = (
                Decimal("5.00")
                if product.mrp <= Decimal("1000.00")
                else Decimal("18.00")
            )

            unit_price = product.base_price
            item_taxable_value = unit_price * qty
            item_tax_amount = item_taxable_value * (gst_rate / Decimal("100.00"))
            item_total = item_taxable_value + item_tax_amount

            # Generate Snapshot
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                item_name=product.name,
                quantity=qty,
                unit_price=unit_price,
                gst_rate_applied=gst_rate,
                item_total=item_total,
            )

            # Smart Logic: Deduct from inventory stock
            product.current_stock -= qty
            product.save()

            # Aggregate Totals
            taxable_value_total += item_taxable_value
            if is_interstate:
                igst_sum += item_tax_amount
            else:
                cgst_sum += item_tax_amount / 2
                sgst_sum += item_tax_amount / 2

        # Final Math (apply manual counter discounts)
        discount = invoice.discount_amount
        grand_total = (taxable_value_total + cgst_sum + sgst_sum + igst_sum) - discount

        # Save calculations to the invoice record
        invoice.taxable_value = taxable_value_total
        invoice.cgst_total = cgst_sum
        invoice.sgst_total = sgst_sum
        invoice.igst_total = igst_sum
        invoice.grand_total = grand_total
        invoice.save()

        return invoice
