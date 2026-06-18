"""URLs da API de envio de e-mail."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from envio_email.api.views import EnvioEmailConteudoViewSet, EnvioEmailViewSet

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
