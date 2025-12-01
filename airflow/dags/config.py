from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

KEY_PATH = "/opt/airflow/dags/snowflake_key.p8"

with open(KEY_PATH, 'rb') as key_file:
    private_key_pem = key_file.read()

private_key = serialization.load_pem_private_key(
    private_key_pem,
    password=None,
    backend=default_backend()
)

private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

SNOWFLAKE_CONFIG = {
    "user": "Luketrmai",
    "account": "jfspetv-wgb43135",
    "private_key": private_key_bytes,
    "warehouse": "COMPUTE_WH",
    "database": "RAW",
    "schema": "MEDTECH_RAW"
}
