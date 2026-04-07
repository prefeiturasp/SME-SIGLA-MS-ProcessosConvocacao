"""
URL configuration for the processes module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessoConvocacaoViewSet
from .views.processos import AtualizarPassoProcessoView
from .views.cargos import CargoProcessoViewSet
from .views.carta_convocacao import CartaConvocacaoViewSet

router = DefaultRouter()
router.register(r'processos-convocacao', ProcessoConvocacaoViewSet)
router.register(r'processos-convocacao/(?P<processo_pk>[^/.]+)/cargos', CargoProcessoViewSet, basename='processo-cargos')
router.register(r'carta-convocacao', CartaConvocacaoViewSet, basename='carta-convocacao')

urlpatterns = [
    path('processos/atualizar-passo/', AtualizarPassoProcessoView.as_view(), name='processos-atualizar-passo'),
    path('', include(router.urls)),
] 