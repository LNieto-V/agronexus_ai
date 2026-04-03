from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, system, iot, dashboard, auth
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgroNexus AI", version="0.1.0")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Routers
app.include_router(system.router)
app.include_router(chat.router)
app.include_router(iot.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
