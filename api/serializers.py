from django.contrib.auth.models import User
from rest_framework import serializers
from products.models import Product, Group, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'name', 'url')


class ProductWithLessonsSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'lessons')


class ProductSerializer(serializers.ModelSerializer):
    num_lessons = serializers.SerializerMethodField()

    def get_num_lessons(self, obj):
        return obj.lessons.count()

    class Meta:
        lessons = LessonSerializer(many=True)
        model = Product
        fields = (
            "id",
            "author",
            "name",
            "start_date",
            "price",
            "num_lessons",
        )
