from django.db import models
from django.contrib.auth.models import User

class Doc(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fastapi_doc_id = models.IntegerField(null=True)
    size = models.FloatField()
    file_path = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Doc {self.id} - {self.file.name if self.file else 'No File'}"

    class Meta:
        db_table = 'docs'

class UsersToDocs(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    docs_id = models.ForeignKey(Doc, on_delete=models.CASCADE)

    def str(self):
        return f"User {self.username} - Doc {self.doc_id}"

    class Meta:
        db_table = 'user_to_docs'

class Price(models.Model):
    file_type = models.CharField(max_length=10)  # расширение файла
    price = models.FloatField()  # цена анализа 1 Кб данных

    def str(self):
        return f"{self.file_type} - {self.price} руб./КБ"

    class Meta:
        db_table = 'price'

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    doc = models.ForeignKey(Doc, on_delete=models.CASCADE)
    order_price = models.FloatField()
    payment = models.BooleanField(default=False)

    def str(self):
        return f"Cart for User {self.user_id} - Doc {self.doc_id} - Paid: {self.payment}"

    class Meta:
        db_table = 'cart'