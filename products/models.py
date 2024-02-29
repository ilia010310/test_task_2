from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count


class GroupError(ValidationError):
    def __init__(self, message="Группы все заполнены"):
        self.message = message
        super().__init__(self.message)


class ProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('lessons').annotate(
            num_lessons=Count('lessons')
        )


class Product(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='products'
    )
    name = models.CharField(max_length=40, verbose_name='Название продукта')
    start_date = models.DateTimeField(verbose_name='Дата и время старта')
    price = models.PositiveIntegerField(verbose_name='Цена')
    subscribers = models.ManyToManyField(User,
                                         through='Access',
                                         related_name='subscribed_products')
    min_users = models.PositiveIntegerField(verbose_name='Минимальное количество участников')
    max_users = models.PositiveIntegerField(verbose_name='Максимальное количество участников')

    objects = ProductManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['id']


class Lesson(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Продукт'
    )
    name = models.CharField(
        max_length=40,
        verbose_name='Название'
    )
    url = models.URLField(verbose_name='Ссылка на видео')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['id']


class Group(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Продукт'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название группы'
    )
    students = models.ManyToManyField(
        User,
        verbose_name='Студенты',
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['id']


class Access(models.Model):
    """Модель, отвечающая за доступ
    пользователя к продукту"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='access')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'product'),
                name='user_product_unique'
            )
        ]

    def __str__(self):
        return f'Разрешение для {self.user}: {self.product}'

    class Meta:
        verbose_name = 'Разрешение'
        verbose_name_plural = 'Разрешения'
        ordering = ['id']


@receiver(post_save, sender=Access)
def assign_user_to_group(sender, instance, created, **kwargs):
    """
    Сигнал, который вызывается при сохранении экземпляра Access.
    Распределяет пользователя в группу при получении доступа к продукту.
    """
    if not created:
        return

    product = instance.product
    user = instance.user

    groups = product.groups.annotate(num_students=Count('students')).order_by('num_students')
    # Находим группу с минимальным количеством студентов
    min_group = groups.first()
    try:
        if min_group.product.max_users == min_group.students.count():
            # Если минимальная группа уже полная
            raise GroupError()  # Вызываем ошибку и обрабатываем ее
        else:
            for group in groups[::-1]:  # А если места еще есть:
                if group.product.max_users == group.students.count():
                    continue  # Пропускаем заполненную группу
                else:
                    group.students.add(user)  # И добавляем в незаполненную группу
                    break  # останавливаем цикл
    except Exception as e:
        print(f"Произошла ошибка: {e}. "
              f"Надо куда то определить пользователя {user}")
        # Какая бы ошибка не произошла - мы ее обрабатываем и пользователь
        # не должен остаться без продукта
