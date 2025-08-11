"""
Django management command to create sample processos.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from processos.models import ProcessoConvocacao
import uuid
import random


class Command(BaseCommand):
    help = 'Cria processos de convocação de exemplo para desenvolvimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Número de processos a serem criados (padrão: 5)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(
            self.style.SUCCESS(f'Criando {count} processos com valores aleatórios...')
        )
        
        processos_criados = []
        
        for i in range(count):
            # Gerar valores aleatórios para os campos com choices
            # Status aleatório
            status_choices = [choice[0] for choice in ProcessoConvocacao.PROCESSO_STATUS_CHOICES]
            random_status = random.choice(status_choices)
            
            # Tipo de processo aleatório
            tipo_choices = [choice[0] for choice in ProcessoConvocacao.PROCESSO_TIPOS_CHOICES]
            random_tipo = random.choice(tipo_choices)
            
            # Descrição aleatória
            descricao_choices = [choice[0] for choice in ProcessoConvocacao.DESCRICAO_TIPOS_CHOICES]
            random_descricao = random.choice(descricao_choices)
            
            processo = ProcessoConvocacao.objects.create(
                concurso_uuid=uuid.uuid4(),
                concurso_nome=f'Concurso de Exemplo {i+1}',
                descricao=random_descricao,
                tipo_processo=random_tipo,
                status=random_status,
                data_publicacao=timezone.now(),
                data_convocacao=timezone.now(),
                numero_convocados=i+1
            )
            processos_criados.append(processo)
            
            # Mostrar informações do processo criado
            status_display = dict(ProcessoConvocacao.PROCESSO_STATUS_CHOICES)[random_status]
            tipo_display = dict(ProcessoConvocacao.PROCESSO_TIPOS_CHOICES)[random_tipo]
            descricao_display = dict(ProcessoConvocacao.DESCRICAO_TIPOS_CHOICES)[random_descricao]
            
            self.stdout.write(
                f'  ✓ Criado processo: {processo.concurso_nome} '
                f'(Status: {status_display}, Tipo: {tipo_display}, Descrição: {descricao_display})'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {len(processos_criados)} processos criados com sucesso!'
            )
        ) 