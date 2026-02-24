from django.db import models
from .base import BaseModel
from auditlog.registry import auditlog

ENVIO_STATUS_PENDENTE = 'PENDENTE'
ENVIO_STATUS_SUCESSO = 'SUCESSO'
ENVIO_STATUS_ERRO = 'ERRO'

CARTA_ENVIO_STATUS_CHOICES = [
    (ENVIO_STATUS_PENDENTE, 'Pendente'),
    (ENVIO_STATUS_SUCESSO, 'Sucesso'),
    (ENVIO_STATUS_ERRO, 'Erro'),
]


class CartaConvocacaoCandidato(BaseModel):
    """
    Registro do envio de email da carta de convocação para cada candidato.
    """
    carta_convocacao_historico = models.ForeignKey(
        'CartaConvocacaoHistorico',
        on_delete=models.CASCADE,
        verbose_name="Histórico da Carta",
        related_name='candidatos',
    )
    nome = models.CharField(max_length=200, verbose_name="Nome")
    rf = models.CharField(max_length=20, verbose_name="RF", blank=True)
    email = models.EmailField(verbose_name="Email")
    status = models.CharField(
        max_length=20,
        choices=CARTA_ENVIO_STATUS_CHOICES,
        verbose_name="Status do envio",
    )
    status_detalhe = models.TextField(
        verbose_name="Detalhe do status",
        blank=True,
        help_text="Mensagem de erro ou detalhe do envio",
    )
    conteudo = models.TextField(
        verbose_name="Conteúdo do email enviado",
        blank=True,
    )

    class Meta:
        verbose_name = "Carta Convocação - Candidato"
        verbose_name_plural = "Carta Convocação - Candidatos"
        ordering = ['-criado_em']
        db_table = 'processos_carta_convocacao_candidato'

    def __str__(self):
        return f"{self.nome} ({self.email}) - {self.get_status_display()}"


auditlog.register(CartaConvocacaoCandidato)
