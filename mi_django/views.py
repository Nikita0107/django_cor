from django.http import HttpResponse
from django.views.decorators.http import require_POST
import requests
from django.shortcuts import render, redirect, get_object_or_404
import os
from django.conf import settings
from PIL import Image, UnidentifiedImageError
from django.contrib.auth import login, authenticate
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Doc, Cart, Price

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически аутентифицируем пользователя после регистрации
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f"Регистрация прошла успешно! Вы вошли как {username}.")
            return redirect('index')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})



@login_required
def index(request):
    docs = Doc.objects.filter(user=request.user)
    return render(request, 'mi_django/index.html', {'docs': docs})

from django.core.files.storage import FileSystemStorage

FASTAPI_BASE_URL = os.environ.get('FASTAPI_BASE_URL', 'http://web:8000')

@login_required
def upload_document(request):
    if request.method == 'POST':
        # Получаем файл из формы
        document_file = request.FILES.get('document')

        if not document_file:
            messages.error(request, "Файл не выбран.")
            return redirect('upload_document')

        # Проверяем, что файл имеет расширение .jpg или .jpeg
        valid_extensions = ['.jpg', '.jpeg']
        ext = os.path.splitext(document_file.name)[1].lower()
        if ext not in valid_extensions:
            error_message = "Ошибка: можно загружать только файлы формата JPEG."
            return render(request, 'mi_django/error_page.html', {'error_message': error_message})

        # Дополнительная проверка содержимого файла с помощью Pillow
        try:
            image = Image.open(document_file)
            if image.format != 'JPEG':
                raise ValueError("Загруженный файл не является JPEG-изображением.")
        except (UnidentifiedImageError, ValueError) as e:
            error_message = "Ошибка: файл не является корректным JPEG-изображением."
            return render(request, 'mi_django/error_page.html', {'error_message': error_message})

        # Сохранение файла локально
        fs = FileSystemStorage()
        filename = fs.save(document_file.name, document_file)
        local_file_path = f"{settings.MEDIA_URL}{filename}"

        # Перемещаем указатель в начале файла после проверки
        document_file.seek(0)

        # Отправляем файл на FastAPI
        response = requests.post(
            f"{FASTAPI_BASE_URL}/upload_doc",
            files={'file': (document_file.name, document_file.read(), document_file.content_type)}
        )

        if response.status_code == 200:
            # Получаем данные из ответа FastAPI
            data = response.json()
            document_id = data.get('id')  # Это ID документа в базе данных FastAPI
            document_name = data.get('name')  # Имя сохранённого файла на стороне FastAPI

            # Сохраняем информацию о документе в базе данных Django
            size = document_file.size / 1024  # Размер в КБ

            doc = Doc.objects.create(
                user=request.user,
                file_path=local_file_path,  # Используем локальный путь
                size=size,
                fastapi_doc_id=document_id
            )

            messages.success(request, "Документ успешно загружен!")
            return redirect('index')
        else:
            messages.error(request, f"Ошибка при загрузке документа: {response.text}")
            return redirect('upload_document')

    return render(request, 'mi_django/upload_document.html')


@login_required
def get_document_text(request, doc_id):
    try:
        doc = Doc.objects.get(id=doc_id, user=request.user)
    except Doc.DoesNotExist:
        return HttpResponse("Документ не найден", status=404)

    # Отправляем запрос на получение текста
    response = requests.get(f"{FASTAPI_BASE_URL}/get_text/{doc.fastapi_doc_id}")

    if response.status_code == 200:
        data = response.json()
        texts = data.get('texts', [])
        # Предполагая, что doc.file_path содержит путь к файлу для скачивания
        file_path = doc.file_path  # Убедитесь, что это поле содержит корректный путь
        return render(request, 'mi_django/document_text.html', {'texts': texts, 'file_path': file_path})
    else:
        return HttpResponse(f"Ошибка при получении текста: {response.text}", status=500)


@login_required
@require_POST
def delete_document(request, doc_id):
    doc = Doc.objects.get(id=doc_id, user=request.user)

    # Определяем путь к файлу
    file_path = os.path.join(settings.MEDIA_ROOT, os.path.basename(doc.file_path))

    # Отправляем запрос на удаление документа в FastAPI
    response = requests.delete(f"{FASTAPI_BASE_URL}/doc_delete/{doc.fastapi_doc_id}")

    # Удаление файла из папки медиа
    if os.path.exists(file_path):
        os.remove(file_path)

    # Удаляем запись из базы данных Django
    doc.delete()
    messages.success(request, "Документ и изображение успешно удалены!")

    return redirect('index')

DEFAULT_PRICE_PER_KB = getattr(settings, 'DEFAULT_PRICE_PER_KB', 1.0)


@login_required
def order_analysis(request, doc_id):
    user = request.user
    # Убедитесь, что документ принадлежит пользователю
    doc = get_object_or_404(Doc, id=doc_id, user=user)

    # Проверяем, не была ли уже произведена оплата
    cart_item = Cart.objects.filter(user=user, doc=doc, payment=True).first()
    if cart_item:
        messages.info(request, "Вы уже оплатили анализ этого документа.")
        return redirect('index')

    # Извлекаем расширение файла из пути к файлу
    file_extension = os.path.splitext(doc.file_path)[1][1:].lower()

    # Получаем цену за КБ для этого типа файла или используем цену по умолчанию
    try:
        price_entry = Price.objects.get(file_type=file_extension)
        price_per_kb = price_entry.price
    except Price.DoesNotExist:
        price_per_kb = DEFAULT_PRICE_PER_KB
        messages.info(request, f"Используется цена по умолчанию для файла '{file_extension}'.")

    # Рассчитываем общую стоимость
    order_price = doc.size * price_per_kb

    if request.method == 'POST':
        # Обработка платежа (здесь необходимо интегрировать платежную систему)
        # После успешной оплаты

        # Используем defaults для передачи обязательных полей при создании
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            doc=doc,
            defaults={
                'order_price': order_price,
                'payment': True  # Предполагая, что оплата успешна
            }
        )
        if not created:
            # Если объект уже существует, обновляем его
            cart_item.order_price = order_price
            cart_item.payment = True
            cart_item.save()

        messages.success(request, "Оплата успешно проведена. Теперь вы можете анализировать документ.")
        return redirect('index')

    return render(request, 'mi_django/order_analysis.html', {'document': doc, 'order_price': order_price})

@login_required
def cart_detail(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    return render(request, 'mi_django/cart_detail.html', {'cart_item': cart_item})

@login_required
def make_payment(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    if request.method == 'POST':

        cart_item.payment = True
        cart_item.save()
        messages.success(request, "Оплата успешно проведена!")
        return redirect('cart_detail', cart_id=cart_item.id)
    else:
        return render(request, 'mi_django/payment_confirmation.html', {'cart_item': cart_item})

@login_required
def cart_list(request):
    cart_items = Cart.objects.filter(user=request.user)
    return render(request, 'mi_django/cart_list.html', {'cart_items': cart_items})


@login_required
@require_POST
def clear_cart(request):
    # Получаем все элементы корзины текущего пользователя
    cart_items = Cart.objects.filter(user=request.user)
    # Удаляем их
    cart_items.delete()
    messages.success(request, "Корзина успешно очищена!")
    return redirect('cart_list')

@login_required
def analyze_document(request, doc_id):
    doc = get_object_or_404(Doc, id=doc_id)

    # Проверяем, является ли пользователь владельцем документа или суперпользователем
    if doc.user != request.user and not request.user.is_superuser:
        messages.error(request, "У вас нет доступа к этому документу.")
        return redirect('index')

    if request.method == 'POST':
        # Проверяем, является ли пользователь суперпользователем
        if request.user.is_superuser:
            # Суперпользователь может выполнить анализ без оплаты
            pass  # Продолжаем с анализом
        else:
            # Обычный пользователь
            # Проверяем, оплатил ли пользователь анализ этого документа
            cart_item = Cart.objects.filter(user=request.user, doc=doc, payment=True).first()
            if not cart_item:
                # Пользователь не оплатил анализ, перенаправляем на страницу оплаты
                messages.error(request, "Сначала оплатите.")
                return redirect('order_analysis', doc_id=doc_id)
            # Пользователь оплатил анализ, продолжаем

        # Отправляем запрос на анализ документа в FastAPI
        response = requests.put(f"{FASTAPI_BASE_URL}/doc_analyse/{doc.fastapi_doc_id}")

        if response.status_code == 200:
            messages.success(request, "Анализ документа запущен!")
        else:
            messages.error(request, f"Ошибка при запуске анализа: {response.text}")

        return redirect('index')
    else:
        # Если GET запрос, можно показать страницу с подтверждением анализа
        return render(request, 'mi_django/confirm_analyze.html', {'doc': doc})