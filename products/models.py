from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count


class GroupError(Exception):
    def __init__(self, message="Группы все заполнены"):
        self.message = message
        super().__init__(self.message)
class Product(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    name = models.CharField(max_length=40, verbose_name='Название продукта')
    start_date = models.DateTimeField(verbose_name='Дата и время старта')
    price = models.PositiveIntegerField(verbose_name='Цена')
    subscribers = models.ManyToManyField(User,
                                         through='Access',
                                         related_name='subscribed_products')
    min_users = models.PositiveIntegerField(verbose_name='Минимальное количество участников')
    max_users = models.PositiveIntegerField(verbose_name='Максимальное количество участников')

    def __str__(self):
        return self.name

    def assign_user_to_group(self, user):
        try:
            # Если продукт уже начался, добавляем пользователя в группы с наименьшим количеством человек
            if self.start_date <= timezone.now():

                # Получаем список групп с подсчетом количества студентов в каждой группе
                groups = self.groups.annotate(num_students=Count('students')).order_by('num_students')
                # Находим группу с минимальным количеством студентов
                min_group = groups.first()
                if min_group.product.max_users == min_group.students.count():
                    raise GroupError()
                else:
                    min_group.students.add(user)
            # Если продукт еще не начался, распределяем пользователей между группами
            else:
                # Получаем список групп, отсортированный по количеству участников
                groups = self.groups.annotate(num_students=Count('students')).order_by('num_students')
                min_group = groups.first()
                # Если минимальная (по количеству челоек) группа заполнена, то все группы переполнены
                if min_group.product.max_users == min_group.students.count():
                    # В дальнейшем либо создавать новую группу,
                    # либо автору закрывать поток при достижении максимума во всех группах
                    raise GroupError()
                else:
                    # Берем максимальную группу, чтобы в первую очередь укомплектовать ее.
                    for group in groups[::-1]:
                        if group.product.max_users == group.students.count():
                            continue
                        else:
                            group.students.add(user)
                            break
        except Exception as e:
            print(f"Произошла ошибка: {e}. Надо куда то определить пользователя {user}")



class Lesson(models.Model):
    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE,
                                related_name='lessons',
                                verbose_name='Продукт')
    name = models.CharField(max_length=40)
    url = models.URLField(verbose_name='Ссылка на видео')

    def __str__(self):
        return self.name


class Group(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='groups',
                                verbose_name='Продукт')
    name = models.CharField(max_length=255, verbose_name='Название группы')
    students = models.ManyToManyField(User, verbose_name='Студенты', blank=True)

    def __str__(self):
        return self.name



class Access(models.Model):
    """Модель, отвечающая за доступ
    пользователя к продукту"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='access')

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f'Разрешение {self.id}'


@receiver(post_save, sender=Access)
def assign_user_to_group(sender, instance, created, **kwargs):
    """
    Сигнал, который вызывается при сохранении экземпляра Access.
    Распределяет пользователя в группу при получении доступа к продукту.
    """
    if created:
        product = instance.product
        user = instance.user
        product.assign_user_to_group(user)
