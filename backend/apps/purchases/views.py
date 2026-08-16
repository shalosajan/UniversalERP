from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PurchaseOrder, Vendor
from .serializers import PurchaseOrderSerializer, VendorSerializer


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def receive(self, request, pk=None):
        """
        Custom Endpoint: /api/purchase-orders/{id}/receive/
        Increases inventory stock and locks the PO status.
        """
        purchase_order = self.get_object()

        # Guardrail: Don't receive an order twice
        if purchase_order.status == "RECEIVED":
            return Response(
                {"error": "This order has already been received."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Iterate through items and add to inventory
        for item in purchase_order.items.all():
            product = item.product
            product.current_stock += item.quantity
            product.save()

        # 2. Update the PO status
        purchase_order.status = "RECEIVED"
        purchase_order.save()

        return Response(
            {
                "message": f"PO-{purchase_order.id} received. Inventory updated successfully."
            }
        )
