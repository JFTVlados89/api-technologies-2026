"""Шаблон REST-сервиса для ДЗ семинара 6.

Ориентир — user-service из семинара 3 (ветка seminar/03-api-interaction).
Можно оставить «пользователей», а можно придумать свою предметную область — Промышленные объекты:
переименуйте модели и пути, но сохраните четыре метода и форму CRUD:

    POST   /v1/facility                   — создать объект, вернуть его идентификатор
    GET    /v1/facility/{facility_id}     — получить объект
    PUT    /v1/facility/{facility_id}     — изменить объект
    DELETE /v1/facility/{facility_id}     — удалить объект

Запуск: uvicorn main:app --reload  →  http://localhost:8000/docs
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --- Модели запросов -------------------------------------------------------
# Каждое поле описывайте через Field с ограничениями (ge/le, min_length,
# max_length, pattern, ...) и examples: CI строит тестовые запросы по схеме
# OpenAPI и в первую очередь берёт значения из examples.


class FacilityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=['Production and warehouse complex'])
    type: str = Field(min_length=1, max_length=50, examples=['factory'])
    price: int = Field(ge=0, le=3_000_000_000,examples=[100000000])



class FacilityUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, examples=["updated"])
    type: Optional[str] = Field(default=None, min_length=1, max_length=50, examples=["updated"])
    price: Optional[int] = Field(default=None, ge=0, le=3_000_000_000, examples=[15000000])

# --- Модели ответов --------------------------------------------------------


class FacilityCreated(BaseModel):
    facility_id: int


class FacilityResponse(FacilityCreated):
    name: str
    type: str
    price: int 


class ErrorResponse(BaseModel):
    detail: str

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Item Service", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # обработка ошибки  
# «База» данных — словарь в памяти: ключ — facility_id, значение — объект.
# Базу данных (SQLite и т. п.) не используем.
facilities: dict[int, FacilityResponse] = {}


@app.post(
    "/v1/facility",
    status_code=201,
    response_model=FacilityCreated,
)
@limiter.limit("3/minute")
async def create_facility(payload: FacilityCreate) -> FacilityCreated:
    new_facility_id = len(facilities) + 1 # создаем уникальный ID объекта
    new_facility = FacilityResponse( # Создаем карточку объекта 
        facility_id = new_facility_id, #достаем из payload ID объекта 
        name = payload.name, #достаем из payload имя объекта 
        type = payload.type, #достаем из payload тип объекта 
        price = payload.price #достаем из payload цену объекта 
    )
    facilities[new_facility_id] = new_facility #Сохраняем наш словарь
    return FacilityCreated(facility_id=new_facility_id) #вывод
#raise HTTPException(status_code=501) -- наша заглушка. Изначальный ошибка 501 Not Implemented "Не реализованно"

@app.get(
    "/v1/facility/{facility_id}",
    response_model=FacilityResponse,
    responses={404: {"model": ErrorResponse, "description": "Item not found"}},
)
async def get_facility(facility_id: int) -> FacilityResponse:
    if facility_id in facilities: # проверка на существование ID объекта
        return facilities[facility_id]
    else:
        raise HTTPException(status_code=404, detail="Facility not found") # Иначе ошибка, что такого объекта не существует  


@app.put(
    "/v1/facility/{facility_id}",
    response_model=FacilityResponse,
    responses={404: {"model": ErrorResponse, "description": "Item not found"}},
)
async def update_facility(facility_id: int, payload: FacilityUpdate) -> FacilityResponse:
    if facility_id not in facilities: #проверяем на его отсутствие 
        raise HTTPException(status_code=404, detail="Facility not changeded")
    
    if payload.name is not None: #проверяем поле name на is not None 
        facilities[facility_id].name = payload.name #изменяем name
    if payload.type is not None: #проверяем поле type на is not None 
        facilities[facility_id].type = payload.type #изменяем type
    if payload.price is not None:  #проверяем поле price на is not None 
        facilities[facility_id].price = payload.price #изменяем price
    return facilities[facility_id] #возвращаем обновленный объект
    

@app.delete(
    "/v1/facility/{facility_id}",
    status_code=204,
    response_model=None,
    responses={404: {"model": ErrorResponse, "description": "Item not found"}},
)
async def delete_facility(facility_id: int) -> None:
    deleted_facility = facilities.pop(facility_id, None)
    if deleted_facility is None:
        raise HTTPException(status_code=404, detail="Facility not deleted")
        
    return