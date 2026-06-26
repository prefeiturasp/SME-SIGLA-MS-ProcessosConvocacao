"""Views da API de envio de e-mail."""

from .views_conteudo import EnvioEmailConteudoViewSet
from .views_envio import EnvioEmailViewSet

__all__ = ["EnvioEmailViewSet", "EnvioEmailConteudoViewSet"]
