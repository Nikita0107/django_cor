from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Doc, UsersToDocs, Cart


"""Тестирование базы данных"""

class DocsTest(TestCase):
    def setUp(self):
        self.doc = Doc.objects.create(
            file_path='test/path/to/file.png',
            size=12345,
            external_id=1,
            file_type='png'
        )

    def test_docs_creation(self):
        self.assertEqual(self.doc.file_path, 'test/path/to/file.png')
        self.assertEqual(self.doc.size, 12345)
        self.assertEqual(self.doc.external_id, 1)
        self.assertEqual(self.doc.file_type, 'png')
        self.assertIsNotNone(self.doc.id)


class UsersToDocsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.doc = Doc.objects.create(
            file_path='test/path/to/file.png',
            size=12345,
            external_id=1,
            file_type='png'
        )
        self.user_to_doc = UsersToDocs.objects.create(
            username=self.user,
            docs_id=self.doc
        )

    def test_users_to_docs_creation(self):
        self.assertEqual(self.user_to_doc.username, self.user)
        self.assertEqual(self.user_to_doc.docs_id, self.doc)
class CartTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.doc = Doc.objects.create(
            file_path='test/path/to/file.png',
            size=12345,
            external_id=1,
            file_type='png'
        )
        self.cart = Cart.objects.create(
            user=self.user,
            docs=self.doc,
            order_price=10,
            payment=False
        )

    def test_cart_creation(self):
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(self.cart.docs, self.doc)
        self.assertEqual(self.cart.order_price, 10)
        self.assertFalse(self.cart.payment)


class UrlsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_login_url(self):
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_home_url(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_doc_url(self):
        url = reverse('add_doc')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
"""Тестирование представлений"""

class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")
        self.test_doc = Doc.objects.create(file_path='test/path/to/file.png', size=12345, external_id=1, file_type='png')

    def test_home_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_delete_doc_page_view(self):
        response = self.client.get(reverse("delete_doc_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "delete_doc.html")

    def test_analyse_doc_view(self):
        doc = Doc.objects.create(file_path="test_path", external_id=999, size=250, file_type="text/plain")
        response = self.client.post(reverse("complete"), {"doc_id": doc.id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "complete.html")
