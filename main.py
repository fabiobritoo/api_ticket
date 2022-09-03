from typing import Union

from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import json
import requests
import pandas as pd
import datetime

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


def ultima_senha(tipo, inicio_expediente):
    df = pd.read_csv("atendimentos.csv")

    ultimo_registro = df[df["Tipo_Senha"] == tipo].tail(1)
    data_ultimo_registro = pd.to_datetime(ultimo_registro["Data_Emissao"]).values[0]

    if data_ultimo_registro < inicio_expediente:
        last_password = 0
    else:
        last_password = int(ultimo_registro["Numeracao"])

    return last_password

def atualizar_tabela(tipo, num):
    ### Obter ID da tabela
    df = pd.read_csv("atendimentos.csv")
    max_id = df.ID.max()
    df = df.append({
            'ID' : max_id + 1
            , 'Tipo_Senha' : tipo
            , 'Numeracao' : num
            , 'Data_Emissao': datetime.datetime.now()
            } , 
            ignore_index = True)
    df.to_csv("atendimentos.csv", index = False)


@app.get("/senha/{tipo}", tags=["Retirar Senha"])
async def retirar_senha(
    tipo: str = Path(title="The ID of the item to get")
):

    ### Análise se o pedido de senha foi feito fora do horário do expediente
    inicio_expediente = pd.to_datetime(datetime.datetime.now().replace(hour = 7, minute = 0, second = 0, microsecond = 0))
    fim_expediente = pd.to_datetime(datetime.datetime.now().replace(hour = 17, minute = 0, second = 0, microsecond = 0))

    horario_atual = pd.to_datetime(datetime.datetime.now())

    if (horario_atual < inicio_expediente) and (horario_atual > fim_expediente):
        return {"senha": "Fora do Expediênte de Trabalho"}

    ### Checar se o tipo é um tipo válido
    tipos_disponiveis = ['SG','SE','SP']
    if tipo not in tipos_disponiveis:
        return {"senha": "Tipo Requisitado não Existe"}  

    ### Checar no banco última senha do tipo
    senha = ultima_senha(tipo, inicio_expediente) + 1
    codigo_senha = tipo + str(senha).zfill(3)
    results = {"senha": codigo_senha}

    ### Atualizar o banco
    atualizar_tabela(tipo, senha)

    return results


@app.get("/", tags=["Root"])
def read_root():
    return {"Abra nassauflix.herokuapp.com/docs para ver as especificações da API"}
