from django.urls import path
from .health import liveness, readiness
from django.http import HttpResponse
from django.urls import reverse

app_name = 'health'

def health_index(request):
    liveness_url = reverse('health:liveness')
    readiness_url = reverse('health:readiness')
    return HttpResponse(f'<a href="{liveness_url}">liveness</a><br><a href="{readiness_url}">readiness</a>')

urlpatterns = [
    path('', health_index, name='health-index'),
    path('liveness/', liveness, name='liveness'),
    path('readiness/', readiness, name='readiness'),
] 