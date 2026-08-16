from rest_framework import viewsets

from .models import Customer, Invoice
from .serializers import CustomerSerializer, InvoiceSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def perform_create(self, serializer):
        """
        Enterprise Guardrail: Automatically assign the logged-in user as the cashier.
        """
        # If the user is logged in, attach them. Otherwise, leave it null.
        cashier = self.request.user if self.request.user.is_authenticated else None
        serializer.save(cashier=cashier)
