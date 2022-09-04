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

import warnings
warnings.filterwarnings("ignore")

from db.connect import connect


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

global con

@app.on_event("startup")
async def startup_event():
   con = connect() 

@app.on_event("shutdown")
def shutdown_event():
    con.close()

def encontrar_senha_por_id(id):
   
    df = pd.read_sql_query('select * from "atendimentos"',con=con)


    codigo_senha = df[df['id']==id].codigo_senha.values[0]
    return codigo_senha

def ultima_senha(tipo, inicio_expediente):
    ## Iniciar Conecção
   
    df = pd.read_sql_query('select * from "atendimentos"',con=con)


    ultimo_registro = df[df["tipo_senha"] == tipo].tail(1)

    if len(ultimo_registro) == 0:
        last_password = 0
        return last_password

    data_ultimo_registro = pd.to_datetime(ultimo_registro["data_emissao"]).values[0]

    if data_ultimo_registro < inicio_expediente:
        last_password = 0
    else:
        last_password = int(ultimo_registro["numeracao"])

    return last_password


def update_column(id, new_value, column_name,table_name):
    cur = con.cursor()

    sql = f"""    
    UPDATE {table_name} 
    SET  {column_name} = '{new_value}'
    Where id = {id}
    """    
    cur.execute(sql)
    con.commit()
    count = cur.rowcount
    print(count, "Record updated successfully into mobile table")

def atualizar_tabela_atendimento(id, guiche):
    ### Obter id da tabela
       
    df = pd.read_sql_query('select * from "atendimentos"',con=con)


    df.loc[df.id==id,"guiche"] = guiche
    df.loc[df.id==id,"data_atendimento"] = datetime.datetime.now()

    print("Valor do ID:",id)
    update_column(id,guiche,"guiche","atendimentos")
    update_column(id,datetime.datetime.now(),"data_atendimento","atendimentos")


def inserir_linha(tipo, num, codigo_senha):
    ### Obter id da tabela
   
    cur = con.cursor()

    sql = f"""    
    INSERT INTO atendimentos (tipo_senha, numeracao,codigo_senha,data_emissao) 
    VALUES ('{tipo}','{num}','{codigo_senha}','{datetime.datetime.now()}')
    """    
    cur.execute(sql)
    con.commit()
    count = cur.rowcount
    print(count, "Record inserted successfully into mobile table")


@app.get("/ultimassenhas", tags =["Ultimas 5 Senhas Chamadas"])
async def ultimas_senhas():
   
    df = pd.read_sql_query('select * from "atendimentos"',con=con)


    lista = list(df[~df["data_atendimento"].isna()].sort_values(by = "data_atendimento").iloc[-5:]["codigo_senha"])
    return lista

@app.get("/chamada/{guiche}", tags=["Chamada da Próxima Senha"])
async def proxima_senha(
    guiche: str = Path(title="guiche que Chamou a Senha")
):
    ### Senhas SP intercaladas com SE|SG
    ### SE tem prioridade a SG

    ### Checar última senha atendida
    ## Se SE|SG -> Chamar SP
   
    df = pd.read_sql_query('select * from "atendimentos"',con=con)


    ultimo_chamado = df[~df["data_atendimento"].isna()].sort_values(by = "data_atendimento").tail(1)

    ## Definir Prioridade
    if len(ultimo_chamado) == 0:
        prioridade = ['SP','SE','SG']
    else:
        ultimo_tipo_senha = ultimo_chamado["tipo_senha"].values[0]
        if (ultimo_tipo_senha == 'SP'):
            prioridade = ['SE','SG','SP']
        else:
            prioridade = ['SP','SE','SG']

    ## Encontrar id
    chamados_esperando = df[df["data_atendimento"].isna()].sort_values(by = "data_emissao")
    if len(chamados_esperando) == 0:
        return {"senha": "Não há senhas a serem chamadas"} 

    for tipo in prioridade:
        chamados_prioritarios = chamados_esperando[chamados_esperando["tipo_senha"] == tipo].head(1)
        if (len(chamados_prioritarios) != 0):
            id_chamado = chamados_prioritarios.id.values[0]
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
    inserir_linha(tipo, senha, codigo_senha)

    return results


@app.get("/", tags=["Root"])
def read_root():
    return {"Abra ticketprint.herokuapp.com/docs para ver as especificações da API"}
