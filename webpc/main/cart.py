from decimal import Decimal
from .models import Product, Cart as DBCart, CartItem
from django.conf import settings

class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user if request.user.is_authenticated else None

        if self.user:
            self.db_cart, _ = DBCart.objects.get_or_create(user=self.user)
            self.cart = None
        else:
            cart = self.session.get(settings.CART_SESSION_ID)
            if not cart:
                cart = self.session[settings.CART_SESSION_ID] = {}
            self.cart = cart
            self.db_cart = None
    
    def add(self, product, quantity=1, override_quantity=False):
        if self.user:
            item, created = CartItem.objects.get_or_create(
                cart=self.db_cart,
                product=product,
                defaults={'price': product.discount_price or product.price, 'quantity': 0}
            )
            if override_quantity:
                item.quantity = quantity
            else:
                item.quantity += quantity
            item.save()
        else:
            product_id = str(product.id)
            if product_id not in self.cart:
                self.cart[product_id] = {
                    'quantity': 0,
                    'price': str(product.discount_price or product.price)
                }
        
            if override_quantity:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.cart[product_id]['quantity'] += quantity
            self.save()
    
    def save(self):
        if not self.user:
            self.session.modified = True

    def remove(self, product):
        if self.user:
            CartItem.objects.filter(cart=self.db_cart, product=product).delete()
        else:
            product_id = str(product.id)
            if product_id in self.cart:
                del self.cart[product_id]
                self.save()
    
    def __iter__(self):
        if self.user:
            for item in self.db_cart.items.select_related('product'):
                yield {
                    'product': item.product,
                    'quantity': item.quantity,
                    'price': item.price,
                    'total_cost': item.get_cost(),
                }
        else:
            product_ids = self.cart.keys()
            products = Product.objects.filter(id__in=product_ids)
            cart = self.cart.copy()
            for product in products:
                cart[str(product.id)]['product'] = product
            for item in cart.values():
                item['price'] = Decimal(item['price'])
                item['total_cost'] = item['price'] * item['quantity']
                yield item

    def __len__(self):
        if self.user:
            return sum(i.quantity for i in self.db_cart.items.all())
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        if self.user:
            return self.db_cart.get_total_price()
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
    
    def clear(self):
        if self.user:
            self.db_cart.items.all().delete()
        else:
            del self.session[settings.CART_SESSION_ID]
            self.save()
