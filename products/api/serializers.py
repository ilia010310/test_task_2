from rest_framework import serializers
from products.models import Product, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'name', 'url')




class ProductListSerializer(serializers.ModelSerializer):
    num_lessons = serializers.IntegerField()

    class Meta:
        model = Product
        fields = (
            'id',
            'author',
            'name',
            'start_date',
            'price',
            "num_lessons",
        )


class ProductDetailSerializer(ProductListSerializer):
    lessons = LessonSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'author', 'name', 'start_date', 'price', 'lessons', 'num_lessons')

