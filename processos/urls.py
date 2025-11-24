"""
URL configuration for the processes module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessoConvocacaoViewSet
from .views.cargos import CargoProcessoViewSet

router = DefaultRouter()
router.register(r'processos-convocacao', ProcessoConvocacaoViewSet)
router.register(r'processos-convocacao/(?P<processo_pk>[^/.]+)/cargos', CargoProcessoViewSet, basename='processo-cargos')

urlpatterns = [
    path('', include(router.urls)),
] 