from django.urls import path
from .health import liveness, readiness
from .views import CustomLoginView, CustomLogoutView

app_name = 'common'

urlpatterns = [
    path('liveness/', liveness, name='liveness'),
    path('readiness/', readiness, name='readiness'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
] 