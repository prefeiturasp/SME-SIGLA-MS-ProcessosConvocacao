"""
Django management command to clear all processos and cargos.
"""

from django.core.management.base import BaseCommand

from processos.models import CargoProcesso, ProcessoConvocacao


class Command(BaseCommand):
    help = "Remove todos os registros das tabelas de processos e cargos"

    def handle(self, *args, **options):
        # Contar registros existentes
        total_processos = ProcessoConvocacao.objects.count()
        total_cargos = CargoProcesso.objects.count()
        total_registros = total_processos + total_cargos

        self.stdout.write(
            self.style.SUCCESS(f"Removendo {total_registros} registros...")
        )
        self.stdout.write(f"  - Processos: {total_processos}")
        self.stdout.write(f"  - Cargos: {total_cargos}")

        try:
            # Remover cargos primeiro (devido à dependência FK)
            if total_cargos > 0:
                self.stdout.write("🗑️  Removendo cargos...")
                CargoProcesso.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {total_cargos} cargos removidos!")
                )

            # Remover processos
            if total_processos > 0:
                self.stdout.write("🗑️  Removendo processos...")
                ProcessoConvocacao.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {total_processos} processos removidos!"
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {total_registros} registros removidos com sucesso!"
                )
            )

            # Verificar se realmente foi limpo
            processos_restantes = ProcessoConvocacao.objects.count()
            cargos_restantes = CargoProcesso.objects.count()

            if processos_restantes == 0 and cargos_restantes == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        "✅ Todas as tabelas completamente limpas!"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Ainda restam {processos_restantes} processos e {cargos_restantes} cargos."  # noqa: E501
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro ao remover registros: {e}")
            )
