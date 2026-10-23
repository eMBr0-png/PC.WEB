from django.db import models
from django.urls import reverse
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField('Имя', max_length=50, db_index=True)
    slug = models.SlugField('Slug', unique=True, max_length=50)
    description = models.CharField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:product_list_by_category', args=[self.slug])

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, verbose_name='Категория')
    name = models.CharField('Имя', max_length=20)
    slug = models.SlugField('Slug', max_length=20, unique=100)
    description = models.CharField('Описание', blank=True)
    price = models.DecimalField('Стоимость', max_digits=10, decimal_places=2)
    discount_price = models.DecimalField('Скидочная стоимость', max_digits=10, decimal_places=2)
    available = models.BooleanField('Доступность', default=False)
    image = models.ImageField('Фото', upload_to='media/%Y/%m/%d', blank=True)
    created = models.DateTimeField('Создан', auto_now_add=True)
    updated = models.DateTimeField('Обновлен', auto_now=True)
    quantity = models.PositiveIntegerField('Количество', default=0)

    class Meta:
        ordering=['-created']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

    def get_discount_percent(self):
        if self.discount_price:
            return int(100 - (self.discount_price * 100 / self.price))
        return 0

    def get_absolute_url(self):
        return reverse('main:product_detail', args=[self.id, self.slug])

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created = models.DateTimeField('Создан', auto_now_add=True)
    updated = models.DateTimeField('Обновлен', auto_now=True)

    class Meta:
        ordering = ['user']
        verbose_name = 'Корзина'

    def __str__(self):
        return f'Корзина пользователя {self.user.username}'
    
    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())

    def __len__(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='products', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Стоимость', max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('cart', 'product')

    def get_cost(self):
        return self.price * self.quantity

    @property
    def total_cost(self):
        return self.get_cost()

class Order(models.Model):
    first_name = models.CharField('Имя', max_length=50)
    last_name = models.CharField('Фамилия', max_length=50)
    paid = models.BooleanField('Оплачено', default=False)
    created = models.DateTimeField('Создан', auto_now_add=True)
    updated = models.DateTimeField('Обновлен', auto_now=True)
    email = models.EmailField('Почта')
    phone = models.CharField('Номер телефона', max_length=20)
    city = models.CharField('Город', max_length=100)
    postal_code = models.CharField('Почтовый индекс', max_length=20)
    address = models.CharField('Адрес', max_length=250)
    user = models.ForeignKey('auth.User', related_name='orders', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created']
    
    def __str__(self):
        return f'Заказ {self.id}'
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', default=1)

    def __str__(self):
        return str(self.id)
    
    def get_cost(self):
        return self.price * self.quantity
