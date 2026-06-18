"""Views da API de envio de e-mail."""

from envio_email.api.views_envio import EnvioEmailViewSet
from envio_email.api.views_conteudo import EnvioEmailConteudoViewSet

__all__ = ["EnvioEmailViewSet", "EnvioEmailConteudoViewSet"]
