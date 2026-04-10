import logging
import time
import json
import uuid
import threading

_thread_locals = threading.local()
logger = logging.getLogger('django.request_logger')


def get_correlation_id():
    return getattr(_thread_locals, 'correlation_id', None)


def get_auth_header():
    print(getattr(_thread_locals, 'auth_header', None))
    return getattr(_thread_locals, 'auth_header', None)

logger = logging.getLogger('django.request_logger')


class AuditlogJWTMiddleware:
    """
    Substitui o AuditlogMiddleware padrão resolvendo o usuário diretamente
    do token JWT antes de setar o actor do auditlog.

    O AuditlogMiddleware padrão lê request.user no nível do middleware, mas
    a autenticação JWT do DRF só resolve o usuário no nível da view — por isso
    o auditlog registrava sempre "system" (AnonymousUser).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = self._resolve_user(request)
        if user and user.is_authenticated:
            from auditlog.context import set_actor
            with set_actor(user):
                return self.get_response(request)
        return self.get_response(request)

    def _resolve_user(self, request):
        try:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            result = JWTAuthentication().authenticate(request)
            if result is not None:
                return result[0]  # (user, token)
        except Exception:
            pass
        return None


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        cid = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        _thread_locals.correlation_id = cid
        print("############ autorização ############")
        print(request.headers.get('Authorization'))
        _thread_locals.auth_header = request.headers.get('Authorization')

        # --- EXTRAÇÃO DO PAYLOAD ---
        payload = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # Verificamos se é JSON para tentar parsear
                if request.content_type == 'application/json' and request.body:
                    payload = json.loads(request.body)
                else:
                    # Para outros tipos (form-data), pegamos o que for possível
                    payload = request.POST.dict() or request.body.decode('utf-8', errors='replace')
            except Exception:
                payload = "<erro_ao_ler_payload>"

        response = self.get_response(request)

        if request.method != 'OPTIONS':
            duration = (time.perf_counter() - start_time) * 1000

            extra_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration, 2),
                'payload': payload,
                'user': str(request.user) if hasattr(request, 'user') else 'Anonymous'
            }
            logger.info(f"{request.method} {request.path}", extra=extra_data)

        response['X-Correlation-ID'] = cid

        _thread_locals.auth_header = None
        _thread_locals.correlation_id = None

        return response