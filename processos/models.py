from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """
    Model base com UUID, criado_em e atualizado_em.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        abstract = True


class ProcessoConvocacao(BaseModel):
    
    PROCESSO_STATUS_CHOICES = [
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('FINALIZADO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    PROCESSO_TIPOS_CHOICES = [
        ('CONVOCACAO', 'Convocação'),
        ('SELECAO', 'Seleção'),
        ('AVALIACAO', 'Avaliação'),
    ]

    DESCRICAO_TIPOS_CHOICES = [
        ('DESCRICAO_CONVOCACAO', 'Convocação'),
        ('DESCRICAO_SELECAO', 'Seleção'),
        ('DESCRICAO_AVALIACAO', 'Avaliação'), 
        ('DESCRICAO_CONVOCACAO_SELECAO', 'Convocação e Seleção'),
    ]
    
    concurso_uuid = models.UUIDField(verbose_name="UUID do Concurso")
    concurso_nome = models.CharField(max_length=200, verbose_name="Nome do Concurso")
    descricao = models.CharField(
        max_length=50,
        choices=DESCRICAO_TIPOS_CHOICES,
        default='DESCRICAO_CONVOCACAO',
        verbose_name="Descrição"
    )
    tipo_processo = models.CharField(
        max_length=20,
        choices=PROCESSO_TIPOS_CHOICES,
        default='CONVOCACAO',
        verbose_name="Tipo de Processo"
    )
    status = models.CharField(
        max_length=20,
        choices=PROCESSO_STATUS_CHOICES,
        default='EM_ANDAMENTO',
        verbose_name="Status"
    )
    data_publicacao = models.DateTimeField(verbose_name="Data de Publicação", default=timezone.now)
    data_convocacao = models.DateTimeField(verbose_name="Data de Convocação", default=timezone.now)
    numero_convocados = models.IntegerField(verbose_name="Número de Convocação", default=1)
    

    class Meta:
        verbose_name = "Processo de Convocação"
        verbose_name_plural = "Processos de Convocação"
        ordering = ['-criado_em']
        db_table = 'processos_convocacao'
    
    def __str__(self):
        return f"{self.concurso_nome} - {self.numero_convocados}"
    
