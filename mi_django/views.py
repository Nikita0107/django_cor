from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
import os
from .models import Doc, Cart, Price
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import logging
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

PROXY_BASE_URL = 'http://djangorest:8002'
FASTAPI_BASE_URL = os.environ.get('FASTAPI_BASE_URL', 'http://web:8000')

logger = logging.getLogger(__name__)

@csrf_exempt
def register(request):
    """
    Представление для регистрации нового пользователя.
    """
    logger.debug(f"Вызвано представление регистрации. Метод запроса: {request.method}")
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Получаем данные из формы
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')

            logger.debug(f"Регистрация пользователя: {username}")

            # Отправляем запрос на прокси-сервер для регистрации
            try:
                logger.debug(f"Отправка запроса на регистрацию пользователя {username} на прокси-сервер.")
                response = requests.post(
                    f"{settings.PROXY_BASE_URL}/api/register/",
                    json={'username': username, 'password': password},
                    timeout=10
                )
                logger.debug(f"Получен ответ от прокси-сервера со статусом: {response.status_code}")
                response.raise_for_status()

                # Если регистрация успешна
                logger.info(f"Пользователь {username} успешно зарегистрирован через прокси-сервер.")
                messages.success(request, f"Регистрация прошла успешно! Теперь вы можете войти.")
                return redirect('login')  # Перенаправляем на страницу входа

            except requests.HTTPError as e:
                logger.error(f"HTTPError during registration for user {username}: {e}")
                messages.error(request, "Ошибка при регистрации на сервере. Попробуйте еще раз.")
            except requests.ConnectionError:
                logger.error(f"ConnectionError during registration for user {username}.")
                messages.error(request, "Не удалось подключиться к серверу. Проверьте соединение.")
            except requests.Timeout:
                logger.error(f"Timeout during registration for user {username}.")
                messages.error(request, "Превышено время ожидания ответа от сервера.")
            except Exception as e:
                logger.error(f"Unexpected error during registration for user {username}: {e}")
                messages.error(request, "Произошла непредвиденная ошибка.")
        else:
            logger.warning(f"Форма регистрации невалидна: {form.errors}")
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = UserRegisterForm()
        logger.debug("Отображение формы регистрации.")

    return render(request, 'registration/register.html', {'form': form})


@csrf_exempt
def login_view(request):
    """
    Кастомное представление для аутентификации пользователя через прокси-сервер.
    """
    logger.debug(f"Вызвано представление входа. Метод запроса: {request.method}")
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        logger.debug(f"Попытка входа пользователя: {username}")

        if not username or not password:
            logger.warning("Имя пользователя или пароль не предоставлены.")
            messages.error(request, "Имя пользователя и пароль обязательны.")
            return render(request, 'registration/login.html')

        try:
            # Отправляем запрос на REST-сервер
            logger.debug(f"Отправка запроса на аутентификацию пользователя {username} на прокси-сервер.")
            response = requests.post(
                f"{settings.PROXY_BASE_URL}/api/login/",
                json={'username': username, 'password': password},
                timeout=10
            )
            logger.debug(f"Получен ответ от прокси-сервера со статусом: {response.status_code}")
            response.raise_for_status()  # Проверяем на ошибки HTTP

            # Получаем токены
            tokens = response.json()
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')

            if not access_token or not refresh_token:
                logger.error(f"Токены не получены для пользователя {username}. Ответ: {tokens}")
                messages.error(request, "Ошибка аутентификации. Токены не получены.")
                return render(request, 'registration/login.html')

            # Логируем токены (временно, только для отладки)
            logger.debug(f"Access Token для {username}: {access_token}")
            logger.debug(f"Refresh Token для {username}: {refresh_token}")

            # Проверяем, существует ли пользователь
            user, created = User.objects.get_or_create(username=username)
            if created:
                logger.info(f"Создан новый пользователь {username} в базе данных Django.")
            else:
                logger.info(f"Пользователь {username} найден в базе данных Django.")

            # Устанавливаем пользовательскую сессию
            login(request, user)
            logger.debug(f"Пользователь {username} вошел в систему.")

            # Сохраняем токены в сессии
            request.session['access_token'] = access_token
            request.session['refresh_token'] = refresh_token
            logger.debug(f"Токены пользователя {username} сохранены в сессии.")

            messages.success(request, f"Добро пожаловать, {username}!")
            return redirect('index')

        except requests.HTTPError as e:
            logger.error(f"HTTPError during login for user {username}: {e}")
            messages.error(request, "Ошибка при аутентификации. Проверьте имя пользователя и пароль.")
        except requests.RequestException as e:
            logger.error(f"RequestException during login for user {username}: {e}")
            messages.error(request, "Ошибка подключения к серверу.")

    else:
        logger.debug("Отображение формы входа.")

    # Если GET или ошибка POST, отобразить форму
    return render(request, 'registration/login.html')


@login_required
def index(request):
    logger.debug(f"Вызвано представление index пользователем: {request.user.username}")
    docs = Doc.objects.filter(user=request.user)
    logger.debug(f"Найдено {docs.count()} документов для пользователя {request.user.username}.")
    return render(request, 'mi_django/index.html', {'docs': docs})


@login_required
def upload_document(request):
    logger.debug(f"Вызвано представление загрузки документа пользователем: {request.user.username}")
    if request.method == "POST":
        logger.debug("Получен POST-запрос на загрузку документа.")
        # Получаем файл из формы
        file = request.FILES.get("document")

        if not file:
            logger.warning("Файл для загрузки не выбран пользователем.")
            messages.error(request, "Файл не выбран.")
            return redirect('upload_document')

        logger.debug(f"Получен файл: {file.name} размером {file.size} байт.")

        # Сохраняем файл локально
        try:
            file_path = default_storage.save(file.name, ContentFile(file.read()))
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            size_kb = file.size / 1024
            logger.info(f"Файл {file.name} сохранён на сервере по пути {full_file_path}. Размер: {size_kb} КБ.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла {file.name}: {e}")
            messages.error(request, "Ошибка при сохранении файла.")
            return redirect('upload_document')

        # Получаем токены из сессии
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')

        if not access_token or not refresh_token:
            logger.error("Ошибка аутентификации: токены отсутствуют в сессии.")
            messages.error(request, "Ошибка аутентификации: необходимо войти в систему.")
            return redirect('login')

        logger.debug("Токены успешно извлечены из сессии.")

        # Формируем заголовки с токеном
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        def make_upload_request():
            # Отправляем файл на сервер
            logger.info(f"Отправка файла {file.name} на прокси-сервер...")
            with open(full_file_path, 'rb') as f:
                try:
                    response = requests.post(
                        f"{settings.PROXY_BASE_URL}/api/upload_doc/",
                        files={'file': (file.name, f, file.content_type)},
                        headers=headers,
                        timeout=10
                    )
                    logger.debug(f"Получен ответ от прокси-сервера со статусом: {response.status_code}")
                    return response
                except Exception as e:
                    logger.error(f"Ошибка при отправке файла {file.name} на прокси-сервер: {e}")
                    raise

        try:
            response = make_upload_request()
            # Проверяем статус ответа
            if response.status_code == 401:
                logger.warning("Токен доступа истёк. Пытаемся обновить токен.")
                # Попытаемся обновить токен
                try:
                    refresh_response = requests.post(
                        f"{settings.PROXY_BASE_URL}/api/token/refresh/",
                        data={'refresh': refresh_token},
                        timeout=10
                    )
                    logger.debug(f"Получен ответ от прокси-сервера при обновлении токена со статусом: {refresh_response.status_code}")

                    if refresh_response.status_code == 200:
                        new_tokens = refresh_response.json()
                        access_token = new_tokens.get('access')
                        if not access_token:
                            logger.error("Не удалось получить новый токен доступа при обновлении.")
                            messages.error(request, "Ошибка аутентификации. Пожалуйста, войдите снова.")
                            return redirect('login')

                        # Обновляем токен в сессии
                        request.session['access_token'] = access_token
                        headers['Authorization'] = f'Bearer {access_token}'

                        logger.info("Токен доступа успешно обновлён.")

                        # Повторяем запрос загрузки файла с новым токеном
                        response = make_upload_request()
                        response.raise_for_status()
                    else:
                        # Не удалось обновить токен
                        logger.error("Не удалось обновить токен доступа. Статус ответа: {refresh_response.status_code}")
                        messages.error(request, "Сессия истекла. Пожалуйста, войдите снова.")
                        return redirect('login')

                except Exception as e:
                    logger.error(f"Ошибка при обновлении токена доступа: {e}")
                    messages.error(request, "Ошибка при обновлении токена. Пожалуйста, войдите снова.")
                    return redirect('login')
            else:
                # Если статус не 401, проверяем на другие ошибки
                response.raise_for_status()

        except requests.RequestException as e:
            logger.error(f"Ошибка при загрузке документа на сервер: {e}")
            messages.error(request, f"Ошибка при загрузке документа: {str(e)}")
            return redirect('upload_document')
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при загрузке документа: {e}")
            messages.error(request, "Произошла ошибка при загрузке документа.")
            return redirect('upload_document')

        # Обрабатываем успешный ответ
        try:
            data = response.json()
            logger.debug(f"Ответ от сервера при загрузке документа: {data}")
            document_id = data.get('id')  # ID документа в FastAPI
            document_url = data.get('url')  # URL изображения от FastAPI
        except ValueError:
            logger.error("Ошибка: не удалось декодировать JSON-ответ от сервера.")
            messages.error(request, "Ошибка при обработке ответа от сервера.")
            return redirect('upload_document')

        # Сохраняем информацию о документе в базе данных Django
        try:
            Doc.objects.create(
                user=request.user,
                file_path=file_path,  # Путь к локальному файлу
                size=size_kb,  # Размер в КБ
                fastapi_doc_id=document_id,
            )
            logger.info(f"Документ {file.name} успешно сохранён в базе данных.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении информации о документе в базе данных: {e}")
            messages.error(request, "Ошибка при сохранении данных документа.")
            return redirect('upload_document')

        logger.info(f"Документ {file.name} успешно загружен. ID документа: {document_id}, URL: {document_url}")
        messages.success(request, "Документ успешно загружен!")
        return redirect('index')

    else:
        logger.debug("Отображение формы загрузки документа.")

    # Если GET-запрос, отображаем форму загрузки
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
        # doc.file_path содержит путь к файлу
        file_path = doc.file_path
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
    requests.delete(f"{FASTAPI_BASE_URL}/doc_delete/{doc.fastapi_doc_id}")

    # Удаление файла из папки медиа
    if os.path.exists(file_path):
        os.remove(file_path)

    # Удаляем запись из базы данных Django
    doc.delete()
    messages.success(request, "Документ и изображение успешно удалены!")

    return redirect('index')

DEFAULT_PRICE_PER_KB = getattr(settings, 'DEFAULT_PRICE_PER_KB', 1.0)

# getattr() используется для получения значения атрибута объекта.
# getattr(object, attribute_name, default_value)

@login_required
def order_analysis(request, doc_id): # заказ_анализ
    user = request.user
    # убедимся что документ принадлежит пользователю
    doc = get_object_or_404(Doc, id=doc_id, user=user)

    # Проверяем, не была ли уже произведена оплата
    cart_item = Cart.objects.filter(user=user, doc=doc, payment=True).first()
    if cart_item:
        messages.info(request, "Вы уже оплатили анализ этого документа.")
        return redirect('index')

    # Извлекаем расширение файла из пути к файлу
    file_extension = doc.file_path.split('.')[-1].lower()
    # Получаем цену за КБ для этого файла
    try:
        price_entry = Price.objects.get(file_type=file_extension)
        price_per_kb = price_entry.price
    except Price.DoesNotExist:
        price_per_kb = DEFAULT_PRICE_PER_KB
        messages.info(request, f"Используется цена по умолчанию для файла '{file_extension}'.")

    # Рассчитываем общую стоимость
    order_price = doc.size * price_per_kb

    if request.method == 'POST':

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
def cart_detail(request, cart_id): # детали корзины
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    return render(request, 'mi_django/cart_detail.html', {'cart_item': cart_item})

# Если объект с указанными параметрами не найден, она автоматически возвращает ошибку HTTP 404 (страница "Не найдено").

@login_required
def make_payment(request, cart_id): # произвести оплату
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    if request.method == 'POST':

        cart_item.payment = True
        cart_item.save()
        messages.success(request, "Оплата успешно проведена!")
        return redirect('cart_detail', cart_id=cart_item.id)
    else:
        return render(request, 'mi_django/payment_confirmation.html', {'cart_item': cart_item})

@login_required
def cart_list(request): # список в корзине
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
        # показать страницу с подтверждением анализа
        return render(request, 'mi_django/confirm_analyze.html', {'doc': doc})