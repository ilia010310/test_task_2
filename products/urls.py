from django.urls import path
from products.api.views import ProductListView, ProductRetrieveView

urlpatterns = [
    path("<int:product_id>/", ProductRetrieveView.as_view(), name="post_detail"),
    path("", ProductListView.as_view(), name="post_list"),
]