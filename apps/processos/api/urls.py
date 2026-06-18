"""URLs da API de processos de convocação."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from processos.api.views import ProcessoConvocacaoViewSet

router = DefaultRouter()
router.register(r"processos-convocacao", ProcessoConvocacaoViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
