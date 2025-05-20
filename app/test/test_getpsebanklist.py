import os
import pytest
from sqlalchemy.orm import Session
from app.payu.services import PayUService
from app.database import SessionLocal

@pytest.fixture(scope="module")
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_pse_bank_list_success(db_session):
    required_env_vars = ["PAYU_ENV_URL", "PAYU_API_LOGIN", "PAYU_API_KEY"]
    missing_vars = [v for v in required_env_vars if not os.getenv(v)]
    if missing_vars:
        pytest(f"Variables de entorno PayU no configuradas: {missing_vars}")

    service = PayUService(db_session)
    response = service.get_pse_bank_list()

    assert response.status_code == 200, f"Status code inesperado: {response.status_code}"

    json_content = response.body.decode()
    assert '"success":true' in json_content.lower(), "La respuesta no indica éxito"

    import json
    content_dict = json.loads(json_content)  # parsear el contenido JSON

    # Por ejemplo, verificar que 'data' contenga una lista
    assert "data" in content_dict
    assert isinstance(content_dict["data"], list)
