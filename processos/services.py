"""
External services for integration with other microservices.
"""
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.exceptions import ValidationError


class ExternalServices:
    """Class for handling external service integrations."""
    
    def __init__(self):
        self.auth_service_url = settings.EXTERNAL_SERVICES['auth_service']['base_url']
        self.notification_service_url = settings.EXTERNAL_SERVICES['notification_service']['base_url']
        self.document_service_url = settings.EXTERNAL_SERVICES['document_service']['base_url']
        self.timeout = settings.EXTERNAL_SERVICES['auth_service']['timeout']
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate user token with auth service."""
        try:
            response = requests.get(
                f"{self.auth_service_url}/api/auth/validate/",
                headers={'Authorization': f'Bearer {token}'},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ValidationError(f"Auth service error: {str(e)}")
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information from auth service."""
        try:
            response = requests.get(
                f"{self.auth_service_url}/api/users/{user_id}/",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ValidationError(f"Auth service error: {str(e)}")
    
    def send_notification(self, message: str, notification_type: str, user_id: str = "system") -> bool:
        """Send notification to notification service."""
        try:
            data = {
                'user_id': user_id,
                'message': message,
                'type': notification_type
            }
            response = requests.post(
                f"{self.notification_service_url}/api/notifications/",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            # Log error but don't fail the main operation
            print(f"Notification service error: {str(e)}")
            return False
    
    def upload_document(self, file_data: bytes, filename: str, metadata: Dict[str, Any]) -> str:
        """Upload document to document service."""
        try:
            files = {'file': (filename, file_data)}
            data = {'metadata': metadata}
            response = requests.post(
                f"{self.document_service_url}/api/documents/upload/",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('file_url', '')
        except requests.RequestException as e:
            raise ValidationError(f"Document service error: {str(e)}")
    
    def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """Get document information from document service."""
        try:
            response = requests.get(
                f"{self.document_service_url}/api/documents/{document_id}/",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ValidationError(f"Document service error: {str(e)}")
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from document service."""
        try:
            response = requests.delete(
                f"{self.document_service_url}/api/documents/{document_id}/",
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Document service error: {str(e)}")
            return False 