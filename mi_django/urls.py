from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('upload-document/', views.upload_document, name='upload_document'),
    path('analyze-document/<int:doc_id>/', views.analyze_document, name='analyze_document'),
    path('get-document-text/<int:doc_id>/', views.get_document_text, name='get_document_text'),
    path('delete-document/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('order-analysis/<int:doc_id>/', views.order_analysis, name='order_analysis'),
    path('cart/', views.cart_list, name='cart_list'),  # Добавленный маршрут
    path('cart/<int:cart_id>/', views.cart_detail, name='cart_detail'),
    path('cart/<int:cart_id>/payment/', views.make_payment, name='make_payment'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)