from django.contrib import admin
from .models import Doc, Price, Cart

@admin.register(Doc)
class DocAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file_path', 'size', 'fastapi_doc_id')
    search_fields = ('user__username', 'file_path')
    list_filter = ('user',)
    ordering = ('-id',)
    readonly_fields = ('id',)

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('file_type', 'price')
    search_fields = ('file_type',)
    ordering = ('file_type',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'doc', 'order_price', 'payment')
    search_fields = ('user__username', 'doc__file_path')
    list_filter = ('payment', 'user')
    ordering = ('-id',)
    readonly_fields = ('id',)

# from .models import UsersToDocs

# @admin.register(UsersToDocs)
# class UsersToDocsAdmin(admin.ModelAdmin):
#     list_display = ('username', 'docs_id')
#     search_fields = ('username__username', 'docs_id__id')
#     ordering = ('-id',)
