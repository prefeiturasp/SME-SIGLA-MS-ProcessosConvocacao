"""
Django management command to create sample processos and cargos.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from processos.models import ProcessoConvocacao, CargoProcesso
from processos.models.constants import PROCESSO_STATUS_CHOICES, TIPO_ESCOLHA_CHOICES
import uuid
import random


class Command(BaseCommand):
    help = 'Cria processos de convocação e cargos de exemplo para desenvolvimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Número de processos a serem criados (padrão: 5)'
        )
        parser.add_argument(
            '--cargos-per-processo',
            type=int,
            default=3,
            help='Número de cargos por processo (padrão: 3)'
        )

    def handle(self, *args, **options):
        count = options['count']
        cargos_per_processo = options['cargos_per_processo']
        
        self.stdout.write(
            self.style.SUCCESS(f'Criando {count} processos com {cargos_per_processo} cargos cada...')
        )
        
        # Lista de 20 concursos pré-definidos
        concursos_disponiveis = [
            {'uuid': uuid.uuid4(), 'nome': 'Concurso Nacional de Tecnologia da Informação'},
            {'uuid': uuid.uuid4(), 'nome': 'Seleção Pública para Desenvolvedores'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso Estadual de Analistas de Sistemas'},
            {'uuid': uuid.uuid4(), 'nome': 'Processo Seletivo para DevOps Engineers'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso Municipal de Desenvolvedores Web'},
            {'uuid': uuid.uuid4(), 'nome': 'Seleção para Arquiteto de Software'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso Federal de Analistas de Dados'},
            {'uuid': uuid.uuid4(), 'nome': 'Processo Seletivo para QA Engineers'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso de Desenvolvedores Mobile'},
            {'uuid': uuid.uuid4(), 'nome': 'Seleção para Tech Lead'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso de Product Managers'},
            {'uuid': uuid.uuid4(), 'nome': 'Processo Seletivo para UX/UI Designers'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso de Scrum Masters'},
            {'uuid': uuid.uuid4(), 'nome': 'Seleção para Business Analysts'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso de Data Scientists'},
            {'uuid': uuid.uuid4(), 'nome': 'Processo Seletivo para Full Stack Developers'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso de Desenvolvedores Backend'},
            {'uuid': uuid.uuid4(), 'nome': 'Seleção para Desenvolvedores Frontend'},
            {'uuid': uuid.uuid4(), 'nome': 'Concurso de Analistas de Infraestrutura'},
            {'uuid': uuid.uuid4(), 'nome': 'Processo Seletivo para Especialistas em Cloud'}
        ]
        
        self.stdout.write(
            self.style.SUCCESS(f'📋 {len(concursos_disponiveis)} concursos disponíveis para seleção aleatória')
        )
        
        # Lista de cargos de exemplo com UUIDs fixos
        cargos_exemplo = [
            {'uuid': uuid.uuid4(), 'nome': 'Analista de Sistemas'},
            {'uuid': uuid.uuid4(), 'nome': 'Desenvolvedor Backend'},
            {'uuid': uuid.uuid4(), 'nome': 'Desenvolvedor Frontend'},
            {'uuid': uuid.uuid4(), 'nome': 'DevOps Engineer'},
            {'uuid': uuid.uuid4(), 'nome': 'Analista de Dados'},
            {'uuid': uuid.uuid4(), 'nome': 'Arquiteto de Software'},
            {'uuid': uuid.uuid4(), 'nome': 'Product Manager'},
            {'uuid': uuid.uuid4(), 'nome': 'UX/UI Designer'},
            {'uuid': uuid.uuid4(), 'nome': 'QA Engineer'},
            {'uuid': uuid.uuid4(), 'nome': 'Tech Lead'},
            {'uuid': uuid.uuid4(), 'nome': 'Scrum Master'},
            {'uuid': uuid.uuid4(), 'nome': 'Business Analyst'},
            {'uuid': uuid.uuid4(), 'nome': 'Data Scientist'},
            {'uuid': uuid.uuid4(), 'nome': 'Mobile Developer'},
            {'uuid': uuid.uuid4(), 'nome': 'Full Stack Developer'},
        ]
        
        self.stdout.write(
            self.style.SUCCESS(f'👥 {len(cargos_exemplo)} cargos disponíveis com UUIDs fixos')
        )
        
        processos_criados = []
        cargos_criados = []
        
        for i in range(count):
            # Escolher um concurso aleatório da lista
            concurso_escolhido = random.choice(concursos_disponiveis)
            
            # Gerar valores aleatórios para os campos com choices
            # Status aleatório
            status_choices = [choice[0] for choice in PROCESSO_STATUS_CHOICES]
            random_status = random.choice(status_choices)
            
            # Tipo de escolha aleatório
            tipo_choices = [choice[0] for choice in TIPO_ESCOLHA_CHOICES]
            random_tipo = random.choice(tipo_choices)
            
            # Descrição aleatória baseada no tipo
            descricoes = {
                'Nova Autorização': f'Convocatório para nova autorização de profissionais',
                'Reposição': f'Processo seletivo para reposição de candidatos',
                'Reconvocação': f'Avaliação técnica para reconvocação de especialistas'
            }
            descricao = descricoes.get(random_tipo, f'Processo de {random_tipo.lower()}')
            
            # Gerar data de convocação aleatória entre 2 e 30 dias a partir de hoje
            dias_aleatorios = random.randint(2, 30)
            data_convocacao = timezone.now() + timezone.timedelta(days=dias_aleatorios)
            
            processo = ProcessoConvocacao.objects.create(
                concurso_uuid=concurso_escolhido['uuid'],
                concurso_nome=concurso_escolhido['nome'],
                descricao=descricao,
                tipo_escolha=random_tipo,
                status=random_status,
                data_convocacao=data_convocacao,
                data_corte_vagas=data_convocacao + timezone.timedelta(days=7)
            )
            processos_criados.append(processo)
            
            # Mostrar informações do processo criado
            status_display = dict(PROCESSO_STATUS_CHOICES)[random_status]
            tipo_display = dict(TIPO_ESCOLHA_CHOICES)[random_tipo]
            
            self.stdout.write(
                f'  ✓ Criado processo: {processo.uuid} '
                f'(Concurso: {processo.concurso_nome[:50]}...) '
                f'(Status: {status_display}, Tipo: {tipo_display}) '
                f'(Convocação: +{dias_aleatorios} dias)'
            )
            
            # Criar cargos para este processo
            cargos_para_processo = random.sample(cargos_exemplo, min(cargos_per_processo, len(cargos_exemplo)))
            
            for j, cargo_info in enumerate(cargos_para_processo):
                cargo = CargoProcesso.objects.create(
                    processo=processo,
                    nome=cargo_info['nome'],
                    cargo_uuid=cargo_info['uuid']  # Usar o UUID fixo do cargo
                )
                cargos_criados.append(cargo)
                
                self.stdout.write(
                    f'    ✓ Cargo {j+1}: {cargo.nome} (UUID: {cargo.cargo_uuid})'
                )
        
        # Mostrar estatísticas finais
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {len(processos_criados)} processos criados com sucesso!'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {len(cargos_criados)} cargos criados com sucesso!'
            )
        )
        
        # Contar concursos únicos utilizados
        concursos_utilizados = set(processo.concurso_uuid for processo in processos_criados)
        self.stdout.write(
            self.style.SUCCESS(
                f'🏆 {len(concursos_utilizados)} concursos únicos utilizados'
            )
        )
        
        # Contar cargos únicos utilizados
        cargos_utilizados = set(cargo.cargo_uuid for cargo in cargos_criados)
        self.stdout.write(
            self.style.SUCCESS(
                f'👥 {len(cargos_utilizados)} cargos únicos utilizados'
            )
        )
        
        # Mostrar concursos utilizados
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Resumo dos concursos utilizados:'
            )
        )
        
        for processo in processos_criados:
            self.stdout.write(
                f'  • {processo.concurso_nome} (UUID: {processo.concurso_uuid})'
            )
        
        # Mostrar cargos utilizados
        self.stdout.write(
            self.style.SUCCESS(
                f'\n👥 Resumo dos cargos utilizados:'
            )
        )
        
        for cargo in cargos_criados:
            self.stdout.write(
                f'  • {cargo.nome} (UUID: {cargo.cargo_uuid})'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Total: {len(processos_criados)} processos + {len(cargos_criados)} cargos'
            )
        ) 