"""
Configuración centralizada del microservicio.
Lee variables de entorno o del archivo .env.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Todas las configuraciones del microservicio en un solo lugar."""

    # --- API Keys ---
    gemini_api_key: str = "AIzaSyBqTTFLRST2xzti0VpWM2HJTO2wg08ibSU"
    stel_api_key: str = "0RjnBmi37UswuylVpjIyi7I6gvX54i2ShBnJLsC0"
    stel_base_url: str = "https://app.stelorder.com/app"

    # --- Email SMTP ---
    smtp_email: str = "incidencias@satgarzon.com"
    smtp_password: str = ""  # Google App Password - se pasa por request

    # --- Fuente de precios ---
    price_source: str = "csv"  # "csv" o "sqlserver"
    csv_prices_path: str = "data/prices_2026.csv"

    # --- SQL Server (futuro, cuando llegue el dongle) ---
    # TODO: Descomentar cuando iQuote tenga datos cargados
    sqlserver_host: str = "192.168.122.81"
    sqlserver_port: int = 1433
    sqlserver_instance: str = "IQUOTE"
    sqlserver_db: str = "iQuote"
    sqlserver_user: str = "sa"
    sqlserver_pass: str = ""

    # --- Constantes de Negocio ---
    washtec_client_id: int = 111
    washtec_discount: float = 10.0
    istobal_client_id: int = 12482218
    istobal_discount: float = 27.0
    istobal_category_id: int = 116398
    portes_id: int = 39320611
    portes_price: float = 15.00
    portes_ref: str = "PPW"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
