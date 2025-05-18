from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path('', views.DeviceListView.as_view(), name='device-list'),
    path('create/', views.DeviceCreateView.as_view(), name='device-create'),
    path('<int:pk>/update/', views.DeviceUpdateView.as_view(), name='device-update'),
    path('<int:pk>/delete/', views.DeviceDeleteView.as_view(), name='device-delete'),
] 