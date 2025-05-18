from django.urls import path
from .health import liveness, readiness

urlpatterns = [
    path('liveness/', liveness, name='liveness'),
    path('readiness/', readiness, name='readiness'),
] 