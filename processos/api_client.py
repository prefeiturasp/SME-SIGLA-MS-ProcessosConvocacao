# import requests
# import json_logging
# from .models import ExternalRequestLog  # Se você for usar o model que criamos

# class ServiceSession(requests.Session):
#     def request(self, method, url, *args, **kwargs):
#         # Tenta recuperar o ID gerado pela biblioteca json-logging
#         # Por padrão, ela armazena isso no contexto da requisição
#         correlation_id = json_logging.get_correlation_id()
        
#         # Injeta o ID nos headers para o próximo microserviço
#         if correlation_id:
#             headers = kwargs.get('headers', {})
#             # Usamos o nome padrão que a lib espera ou o seu X-Correlation-ID
#             headers['X-Correlation-ID'] = correlation_id
#             kwargs['headers'] = headers

#         # Executa a chamada
#         response = super().request(method, url, *args, **kwargs)

# # Instância global para aproveitar o pool de conexões (performance)
# http_client = ServiceSession()
