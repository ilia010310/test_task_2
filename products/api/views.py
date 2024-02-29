from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from products.models import Product
from .serializers import ProductListSerializer, ProductDetailSerializer


class ProductRetrieveView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    lookup_url_kwarg = 'product_id'
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        product_id = self.kwargs['product_id']
        if not self.request.user.subscribed_products.filter(id=product_id).exists():
            raise ValidationError(
                {"error": "You do not have access to this product"},
                code=status.HTTP_403_FORBIDDEN
            )
        return super().get_object()


class ProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer

