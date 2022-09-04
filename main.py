from cgi import print_environ
from typing import Union

from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import json
import requests
import pandas as pd
import numpy as np
import datetime

# uvicorn main:app --reload  

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

def encontrar_senha_por_id(id):
    df = pd.read_csv("atendimentos.csv")
    codigo_senha = df[df['ID']==id].Codigo_Senha.values[0]
    return codigo_senha

def ultima_senha(tipo, inicio_expediente):
    df = pd.read_csv("atendimentos.csv")

    ultimo_registro = df[df["Tipo_Senha"] == tipo].tail(1)

    if len(ultimo_registro) == 0:
        last_password = 0
        return last_password

    data_ultimo_registro = pd.to_datetime(ultimo_registro["Data_Emissao"]).values[0]

    if data_ultimo_registro < inicio_expediente:
        last_password = 0
    else:
        last_password = int(ultimo_registro["Numeracao"])

    return last_password

def atualizar_tabela_atendimento(id, guiche):
    ### Obter ID da tabela
    df = pd.read_csv("atendimentos.csv")

    df.loc[df.ID==id,"Guiche"] = guiche
    df.loc[df.ID==id,"Data_Atendimento"] = datetime.datetime.now()

    df.to_csv("atendimentos.csv", index = False)

def atualizar_tabela(tipo, num, codigo_senha):
    ### Obter ID da tabela
    df = pd.read_csv("atendimentos.csv")
    max_id = df.ID.max()
    if np.isnan(df.ID.max()):
        max_id = 0

    df_new_row = pd.DataFrame(
        [[
            max_id + 1
            ,'SP'
            ,1
            ,'codigo_senha'
            , datetime.datetime.now()
            ]]
        , columns=['ID','Tipo_Senha','Numeracao','Codigo_Senha','Data_Emissao'])

    df = pd.concat([df,df_new_row]).reset_index(drop=True)

    df.to_csv("atendimentos.csv", index = False)

@app.get("/ultimassenhas", tags =["Ultimas 5 Senhas Chamadas"])
async def ultimas_senhas():
    df = pd.read_csv('atendimentos.csv')
    lista = list(df[~df["Data_Atendimento"].isna()].sort_values(by = "Data_Atendimento").iloc[-5:]["Codigo_Senha"])
    return lista

@app.get("/chamada/{guiche}", tags=["Chamada da Próxima Senha"])
async def proxima_senha(
    guiche: str = Path(title="Guiche que Chamou a Senha")
):
    ### Senhas SP intercaladas com SE|SG
    ### SE tem prioridade a SG

    ### Checar última senha atendida
    ## Se SE|SG -> Chamar SP
    df = pd.read_csv('atendimentos.csv')

    ultimo_chamado = df[~df["Data_Atendimento"].isna()].sort_values(by = "Data_Atendimento").tail(1)

    ## Definir Prioridade
    if len(ultimo_chamado) == 0:
        prioridade = ['SP','SE','SG']
    else:
        ultimo_tipo_senha = ultimo_chamado["Tipo_Senha"].values[0]
        if (ultimo_tipo_senha == 'SP'):
            prioridade = ['SE','SG','SP']
        else:
            prioridade = ['SP','SE','SG']

    ## Encontrar ID
    chamados_esperando = df[df["Data_Atendimento"].isna()].sort_values(by = "Data_Emissao")
    if len(chamados_esperando) == 0:
        return {"senha": "Não há senhas a serem chamadas"} 

    for tipo in prioridade:
        chamados_prioritarios = chamados_esperando[chamados_esperando["Tipo_Senha"] == tipo].head(1)
        if (len(chamados_prioritarios) != 0):
            id_chamado = chamados_prioritarios.ID.values[0]
            break

    proxima_senha = encontrar_senha_por_id(id_chamado)

    atualizar_tabela_atendimento(id_chamado, guiche)

    return {
        "senha": proxima_senha
        ,"guiche": guiche} 

@app.get("/senha/{tipo}", tags=["Retirar Senha"])
async def retirar_senha(
    tipo: str = Path(title="Código do Tipo da Senha")
):

    ### Análise se o pedido de senha foi feito fora do horário do expediente
    inicio_expediente = pd.to_datetime(datetime.datetime.now().replace(hour = 7, minute = 0, second = 0, microsecond = 0))
    fim_expediente = pd.to_datetime(datetime.datetime.now().replace(hour = 17, minute = 0, second = 0, microsecond = 0))

    horario_atual = pd.to_datetime(datetime.datetime.now())
    # horario_atual = pd.to_datetime(datetime.datetime.now().replace(hour = 15))

    # if (horario_atual < inicio_expediente) or (horario_atual > fim_expediente):
    #     return {"senha": "Fora do Expediente de Trabalho"}

    ### Checar se o tipo é um tipo válido
    tipos_disponiveis = ['SG','SE','SP']
    if tipo not in tipos_disponiveis:
        return {"senha": "Tipo Requisitado não Existe"}  

    ### Checar no banco última senha do tipo
    senha = ultima_senha(tipo, inicio_expediente) + 1
    codigo_senha = tipo + str(senha).zfill(3)

    data = datetime.datetime.now().strftime("%d/%m/%Y")
    printer_output = data + " " + str(senha).zfill(2)
    results = {
        "senha": codigo_senha
        ,"data": data
        , "printed" : printer_output
        }


    ### Atualizar o banco
    atualizar_tabela(tipo, senha, codigo_senha)

    return results


@app.get("/", tags=["Root"])
def read_root():
    return {"Abra ticketprint.herokuapp.com/docs para ver as especificações da API"}
