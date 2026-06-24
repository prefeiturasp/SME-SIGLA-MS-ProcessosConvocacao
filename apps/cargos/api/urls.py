"""URLs da API de cargos."""

from cargos.api.views import CargoProcessoViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(
    r"processos-convocacao/(?P<processo_pk>[^/.]+)/cargos",
    CargoProcessoViewSet,
    basename="processo-cargos",
)

urlpatterns = [
    path("", include(router.urls)),
]
