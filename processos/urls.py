"""URL configuration for the processes module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProcessoConvocacaoViewSet
from .views.cargos import CargoProcessoViewSet
from .views.envio_email import EnvioEmailViewSet
from .views.envio_email_conteudo import EnvioEmailConteudoViewSet

router = DefaultRouter()
router.register(r"processos-convocacao", ProcessoConvocacaoViewSet)
router.register(
    r"processos-convocacao/(?P<processo_pk>[^/.]+)/cargos",
    CargoProcessoViewSet,
    basename="processo-cargos",
)
router.register(r"envio-email", EnvioEmailViewSet, basename="envio-email")
router.register(
    r"envio-email-conteudo",
    EnvioEmailConteudoViewSet,
    basename="envio-email-conteudo",
)

urlpatterns = [
    path("", include(router.urls)),
]
