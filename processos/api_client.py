import requests
from processos.middlewares import get_auth_header, get_correlation_id


class ServiceSession(requests.Session):
    """
    requests.Session que injeta automaticamente os headers de rastreamento
    e autenticação em todas as chamadas de saída, a partir do contexto
    da thread corrente (capturado pelo CorrelationIdMiddleware).

    Usa setdefault() para nunca sobrescrever headers definidos explicitamente
    pelo chamador.
    """

    def request(self, method, url, *args, **kwargs):
        headers = kwargs.pop('headers', {}) or {}

        if cid := get_correlation_id():
            headers.setdefault('X-Correlation-ID', cid)

        if auth := get_auth_header():
            headers.setdefault('Authorization', auth)

        kwargs['headers'] = headers
        return super().request(method, url, *args, **kwargs)


# Singleton — reutiliza o pool de conexões do urllib3 entre chamadas.
http_client = ServiceSession()
