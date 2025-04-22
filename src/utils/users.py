from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db

# Настройки
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None):
    to_encode = {"user_id": user_id}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


from src.db.models import AllUsersProfilesMain, User


# Функция для получения списка пользователей из базы данных
async def get_users(session: AsyncSession, limit: int, offset: int):
    """Получение списка пользователей"""
    result = await session.execute(
        select(User)
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


from fastapi import Header


async def get_current_user(
        token: str = Header(...),  # Получаем токен из заголовка Authorization
        db: AsyncSession = Depends(get_db),
):
    """Получение текущего пользователя из JWT-токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Недействительный токен")

        user = await db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Невозможно проверить токен")


async def get_user_by_nickname(db: AsyncSession, nickname: str):
    result = await db.execute(select(User).filter(User.nickname == nickname))
    return result.scalars().first()


"""Заметки!!!!-----------------------------------"""
from src.db.models import Note
from pydantic import BaseModel
from datetime import datetime

class NoteBase(BaseModel):
    text: str

class NoteCreate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

async def get_notes_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Note).filter(Note.user_id == user_id))
    return result.scalars().all()

async def create_note(db: AsyncSession, user_id: int, note_data: NoteCreate):
    new_note = Note(user_id=user_id, text=note_data.text)
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note


"""Болезни------------------------------"""
from src.db.models import Disease  # Импортируем модель болезней

from sqlalchemy.future import select

async def add_disease_to_user(db: AsyncSession, user: User, disease_id: int):
    """Добавить болезнь пользователю"""
    disease = await db.get(Disease, disease_id)

    if not disease:
        raise HTTPException(status_code=404, detail="Болезнь не найдена")

    # Проверка, есть ли эта болезнь у пользователя
    if disease in user.diseases:
        raise HTTPException(status_code=400, detail="Болезнь уже добавлена пользователю")

    user.diseases.append(disease)  # Добавляем болезнь в список болезней пользователя
    db.add(user)  # Обязательно добавьте пользователя в сессию
    await db.commit()
    await db.refresh(user)  # Обновляем пользователя после коммита
    return {"msg": "Болезнь добавлена успешно"}









async def get_user_diseases(db: AsyncSession, user_id: int):
    """Получить список болезней пользователя"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return [disease.name for disease in user.diseases]  # Возвращаем список названий болезней


"""Симптомы-------------------------------------------"""
from src.db.models import Symptom, Disease

async def create_symptom(db: AsyncSession, name: str):
    """Создать новый симптом"""
    result = await db.execute(select(Symptom).filter(Symptom.name == name))
    existing_symptom = result.scalars().first()

    if existing_symptom:
        raise HTTPException(status_code=400, detail="Симптом уже существует")

    new_symptom = Symptom(name=name)
    db.add(new_symptom)
    await db.commit()
    await db.refresh(new_symptom)
    return new_symptom

async def link_disease_symptom(db: AsyncSession, disease_id: int, symptom_id: int):
    """Привязать симптом к болезни"""
    disease = await db.get(Disease, disease_id)
    symptom = await db.get(Symptom, symptom_id)

    if not disease or not symptom:
        raise HTTPException(status_code=404, detail="Болезнь или симптом не найдены")

    disease.symptoms.append(symptom)
    await db.commit()
    return {"msg": "Симптом добавлен к болезни"}



async def get_all_diseases(db: AsyncSession):
    """Получить список всех болезней с их описаниями"""
    result = await db.execute(select(Disease))
    diseases = result.scalars().all()
    return [{"id": disease.id, "name": disease.name, "description": disease.description} for disease in diseases]

