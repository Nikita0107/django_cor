from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Doc, Cart
from unittest.mock import patch

class ModelsTestCase(TestCase):
    def setUp(self):
        # Создаём тестового пользователя
        self.user = User.objects.create(username='testuser')

    def test_doc_creation(self):
        """Тест создания объекта Doc"""
        # Создаём тестовый объект Doc
        doc = Doc.objects.create(
            user=self.user,
            file_path='test/path/to/file.png',
            size=12345,
        )
        # Проверяем, что все данные установлены корректно
        self.assertEqual(doc.file_path, 'test/path/to/file.png')
        self.assertEqual(doc.size, 12345)
        self.assertEqual(doc.user.username, 'testuser')  # Проверяем связь с пользователем
        self.assertIsNotNone(doc.id)  # Проверяем, что объект успешно создан

    def test_cart_creation(self):
        """Тест создания объекта Cart"""
        # Создаём тестовый объект Doc
        doc = Doc.objects.create(
            user=self.user,
            file_path='test/path/to/file.png',
            size=12345,
        )
        # Создаём объект корзины (Cart)
        cart = Cart.objects.create(
            user=self.user,
            order_price=10,
            payment=False,
            doc=doc
        )
        # Проверяем, что корзина связана с пользователем
        self.assertEqual(cart.user, self.user)
        # Проверяем, что корзина связана с документом
        self.assertEqual(cart.doc, doc)
        # Проверяем, что цена заказа установлена правильно
        self.assertEqual(cart.order_price, 10)
        # Проверяем, что статус оплаты по умолчанию — False
        self.assertFalse(cart.payment)

class ViewsTestCase(TestCase):
    def setUp(self):
        # Создаём тестового пользователя
        self.user = User.objects.create_user(username='testuser', password='testpass')
        # Логиним пользователя для тестов защищённых маршрутов
        self.client.login(username='testuser', password='testpass')

    def test_login_url(self):
        """Тест доступности страницы входа"""
        url = reverse('login')  # Генерируем URL для входа
        response = self.client.get(url)
        # Проверяем, что страница доступна
        self.assertEqual(response.status_code, 200)

    def test_home_url(self):
        """Тест доступности главной страницы"""
        url = reverse('index')  # Генерируем URL для главной страницы
        response = self.client.get(url)
        # Проверяем, что страница доступна
        self.assertEqual(response.status_code, 200)

    def test_add_doc_url(self):
        """Тест доступности страницы загрузки документа"""
        url = reverse('upload_document')  # Генерируем URL для загрузки документа
        response = self.client.get(url)
        # Проверяем, что страница доступна
        self.assertEqual(response.status_code, 200)

    def test_home_view(self):
        """Тест главной страницы с отображением документов"""
        # Создаём тестовый документ
        _ = Doc.objects.create(
            file_path="path/to/file.png",
            size=12345,
            user=self.user,
            fastapi_doc_id="123"
        )
        # Выполняем GET-запрос
        response = self.client.get(reverse("index"))
        # Проверяем, что страница доступна
        self.assertEqual(response.status_code, 200)
        # Проверяем, что используется правильный шаблон
        self.assertTemplateUsed(response, "mi_django/index.html")

class DocumentActionsTestCase(TestCase):
    def setUp(self):
        # Создаём тестового пользователя
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        # Создаём тестовый документ
        self.doc = Doc.objects.create(
            user=self.user,
            file_path='test_path',
            fastapi_doc_id='1234',
            size=123.45
        )
        # Логиним пользователя
        self.client.login(username='testuser', password='testpassword')

    def test_non_owner_access(self):
        """Тест доступа к документу не владельцем"""
        _ = User.objects.create_user(username='otheruser', password='otherpassword')
        self.client.login(username='otheruser', password='otherpassword')
        response = self.client.get(reverse('analyze_document', args=[self.doc.id]))
        self.assertEqual(response.status_code, 302)

    def test_owner_without_payment(self):
        """Тест: владелец документа без оплаты перенаправляется на оплату"""
        response = self.client.post(reverse('analyze_document', args=[self.doc.id]))
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access(self):
        """Тест доступа суперпользователя к анализу документа"""
        superuser = User.objects.create_superuser(username='admin', password='adminpassword')
        self.client.login(username='admin', password='adminpassword')
        with patch('mi_django.views.requests.put') as mock_put:
            mock_put.return_value.status_code = 200
            response = self.client.post(reverse('analyze_document', args=[self.doc.id]))
            self.assertEqual(response.status_code, 302)

    @patch("mi_django.views.requests.delete")
    def test_delete_document(self, mock_delete):
        """Тест удаления документа"""
        mock_delete.return_value.status_code = 200
        response = self.client.post(reverse("delete_document", args=[self.doc.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Doc.objects.filter(id=self.doc.id).exists())

    @patch("mi_django.views.requests.get")
    def test_get_document_text(self, mock_get):
        """Тест успешного получения текста документа"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'texts': ['Текст 1']}
        response = self.client.get(reverse('get_document_text', args=[self.doc.id]))
        self.assertEqual(response.status_code, 200)

class GetDocumentTextTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.doc = Doc.objects.create(
            user=self.user,
            file_path='test_path',
            fastapi_doc_id='1234',
            size=123.45
        )
        self.url = reverse('get_document_text', args=[self.doc.id])

    def test_document_not_found(self):
        """Документ не найден (404)"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('get_document_text', args=[999]))  # Несуществующий ID
        self.assertEqual(response.status_code, 404)

    def test_successful_text_retrieval(self):
        """Успешное получение текста"""
        self.client.login(username='testuser', password='testpassword')
        with patch('mi_django.views.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'texts': ['Текст 1']}
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

    def test_fastapi_error(self):
        """Ошибка от FastAPI"""
        self.client.login(username='testuser', password='testpassword')
        with patch('mi_django.views.requests.get') as mock_get:
            mock_get.return_value.status_code = 500
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 500)

    def test_no_file_selected(self):
        """Тест без выбранного файла"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('upload_document'))
        self.assertRedirects(response, reverse('upload_document'))

class UploadDocumentTestCase(TestCase):
    def setUp(self):
        """Создаём тестового пользователя и авторизуем его"""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.force_login(self.user)  # Аутентификация пользователя

    @patch('mi_django.views.requests.post')
    def test_successful_image_upload(self, mock_post):
        """Тест успешной загрузки изображения"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'id': '1234'}

        # Тестовый файл изображения
        test_image = SimpleUploadedFile("test.jpg", b"fake_image_content", content_type="image/jpeg")

        response = self.client.post(reverse('upload_document'), {'document': test_image})

        # Ожидаем редирект на главную страницу (index)
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(Doc.objects.filter(fastapi_doc_id='1234').exists())