"""
URL configuration for the processes module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessoConvocacaoViewSet

router = DefaultRouter()
router.register(r'processos-convocacao', ProcessoConvocacaoViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 