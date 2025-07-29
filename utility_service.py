import google.auth.transport.requests
import google.oauth2.id_token


def generate_token(audience) -> str:
    """Generate a Google-signed OAuth ID token"""
    google_auth_request = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(google_auth_request, audience)
    return id_token
