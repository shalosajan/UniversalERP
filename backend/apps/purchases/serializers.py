from rest_framework import serializers
from django.db import transaction
from .models import Vendor, PurchaseOrder, PurchaseItem


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = ["id", "product", "quantity", "unit_cost"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    # This allows us to send the PO and its items in one single JSON payload
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        for item_data in items_data:
            PurchaseItem.objects.create(purchase_order=purchase_order, **item_data)

        # Notice: We removed the inventory update logic here.
        # Stock will now only be updated when the PO status changes to 'RECEIVED' via a custom API endpoint.

        return purchase_order
