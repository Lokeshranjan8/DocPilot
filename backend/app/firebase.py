import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv


class FirebaseConfigurationError(RuntimeError):
    """Raised when the Admin SDK credentials have not been configured."""


def initialize_firebase() -> firebase_admin.App:
    """Initialize Firebase Admin once, when a protected route needs it."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    # Docker supplies these variables with ``env_file``. Loading the local file
    # here also makes ``uvicorn app.main:app --reload`` work outside Docker.
    load_dotenv(Path(__file__).with_name(".env"))
    service_account_path = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH", "app/serviceAccountKey.json"
    )
    credential_path = Path(service_account_path)
    if not credential_path.is_file():
        raise FirebaseConfigurationError(
            "Firebase Admin is not configured. Download a service-account key "
            "to backend/app/serviceAccountKey.json, or set "
            "FIREBASE_SERVICE_ACCOUNT_PATH to its file path."
        )
    credential = credentials.Certificate(credential_path)
    return firebase_admin.initialize_app(credential)
