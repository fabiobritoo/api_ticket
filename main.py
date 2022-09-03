from typing import Union

from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import json
import requests
import re

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

@app.get("/senha/{tipo}", tags=["Retirar Senha"])
async def retirar_senha(
    tipo: int = Path(title="The ID of the item to get"),
    q: Union[str, None] = Query(default=None, alias="item-query"),
):
    results = {"item_id": tipo}
    if q:
        results.update({"q": q})
    return results


@app.get("/", tags=["Root"])
def read_root():
    return {"Abra nassauflix.herokuapp.com/docs para ver as especificações da API"}
