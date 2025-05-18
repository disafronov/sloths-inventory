import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestAuthViews:
    def test_login_view_get(self, client):
        """Тест GET-запроса к странице входа"""
        url = reverse('common:login')
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'username' in response.context['form'].fields
        assert 'password' in response.context['form'].fields

    def test_login_view_post_success(self, client):
        """Тест успешного входа"""
        User.objects.create_user(username='testuser', password='testpass')
        url = reverse('common:login')
        response = client.post(url, {
            'username': 'testuser',
            'password': 'testpass',
        })
        assert response.status_code == 302
        assert response.url == '/'

    def test_login_view_post_invalid(self, client):
        """Тест входа с неверными данными"""
        url = reverse('common:login')
        response = client.post(url, {
            'username': 'wronguser',
            'password': 'wrongpass',
        })
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_logout_view(self, client):
        """Тест выхода из системы"""
        # Сначала входим
        User.objects.create_user(username='testuser', password='testpass')
        client.login(username='testuser', password='testpass')
        
        # Затем выходим
        url = reverse('common:logout')
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('common:login')

    def test_redirect_authenticated_user(self, client):
        """Тест перенаправления авторизованного пользователя"""
        User.objects.create_user(username='testuser', password='testpass')
        client.login(username='testuser', password='testpass')
        
        url = reverse('common:login')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == '/' 