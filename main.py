
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}
KEYS = set(DEFAULTS)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize(layer):
    result = {}
    for key, value in layer.items():
        if value is None:
            continue
        key = str(key).strip().lower()
        if key.startswith("app_"):
            key = key[4:]
        if key == "num_workers":
            key = "workers"
        if key in KEYS:
            result[key] = value
    return result

def typed(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return str(value).strip().lower() in {
            "true", "1", "yes", "on"
        }
    return str(value)

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = dict(DEFAULTS)

    env_name = os.getenv("APP_ENV", "development")
    yaml_path = BASE / f"config.{env_name}.yaml"
    if yaml_path.exists():
        with yaml_path.open(encoding="utf-8") as f:
            config.update(normalize(yaml.safe_load(f) or {}))

    config.update(normalize(dotenv_values(BASE / ".env")))

    os_config = {
        key: value for key, value in os.environ.items()
        if key.startswith("APP_")
    }
    config.update(normalize(os_config))

    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip().lower()
        if key == "num_workers":
            key = "workers"
        if key in KEYS:
            config[key] = value

    result = {key: typed(key, config[key]) for key in KEYS}
    result["api_key"] = "****"
    return result
