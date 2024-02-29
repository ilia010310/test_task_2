from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from .serializers import ProductSerializer, ProductWithLessonsSerializer


class ProductList(APIView):
    def get(self, request, format=None):
        transformers = Product.objects.all()
        serializer = ProductSerializer(transformers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetail(APIView):
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        if not request.user.subscribed_products.filter(id=pk).exists():
            return Response({"error": "You do not have access to this product"}, status=status.HTTP_403_FORBIDDEN)
        product = self.get_object(pk)
        serializer = ProductWithLessonsSerializer(product)
        return Response(serializer.data)

