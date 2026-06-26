"""URLs da API de processos de convocação."""

from django.urls import include, path
from processos.api.views import ProcessoConvocacaoViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"processos-convocacao", ProcessoConvocacaoViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
