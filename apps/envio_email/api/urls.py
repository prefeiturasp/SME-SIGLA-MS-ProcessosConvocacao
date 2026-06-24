"""URLs da API de envio de e-mail."""

from django.urls import include, path
from envio_email.api.views import EnvioEmailConteudoViewSet, EnvioEmailViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"envio-email", EnvioEmailViewSet, basename="envio-email")
router.register(
    r"envio-email-conteudo",
    EnvioEmailConteudoViewSet,
    basename="envio-email-conteudo",
)

urlpatterns = [
    path("", include(router.urls)),
]
