"""Views da API de envio de e-mail."""

from .views_envio import EnvioEmailViewSet
from .views_conteudo import EnvioEmailConteudoViewSet

__all__ = ["EnvioEmailViewSet", "EnvioEmailConteudoViewSet"]
