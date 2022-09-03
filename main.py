from typing import Union

from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import json
import requests
import pandas as pd

# uvicorn main:app --reload  

class Senha(BaseModel):
    tipo: str
    type: Union[str, None] = None
    class Config:
        schema_extra = {
            "example": {
                "tipo": "SP",
                "type": "Filme"
            }
        }
class Platform(BaseModel):
    platform_name: str
    class Config:
        schema_extra = {
            "example": {
                "platform_name": "telecine-play"
            }
        }

app = FastAPI(    
    title='Ticket API',
    description='API desenvolvida para ser utilizada no projeto de Sistemas Distribuidos. Seu objetivo é servir como base para um sistema de entrega de tickets.')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ultima_senha(tipo):
    df = pd.read_csv("atendimentos.csv")
    last_password = int(df[df["Tipo_Senha"] == tipo]["Numeracao"].max())
    return last_password



@app.get("/senha/{tipo}", tags=["Retirar Senha"])
async def retirar_senha(
    tipo: str = Path(title="The ID of the item to get")
):
    tipos_disponiveis = ['SG','SA','SP']
    if tipo not in tipos_disponiveis:
        return {"senha": "Tipo Requisitado não Existe"}
    ###Checar no banco última senha do tipo
    senha = ultima_senha(tipo) + 1
    codigo_senha = tipo + str(senha).zfill(3)
    results = {"senha": codigo_senha}
    return results


@app.get("/", tags=["Root"])
def read_root():
    return {"Abra nassauflix.herokuapp.com/docs para ver as especificações da API"}
