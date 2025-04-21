from fastapi import FastAPI, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from starlette.websockets import WebSocket


from src.db.database import sessionmanager, get_db, get_db_for_websockets

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    sessionmanager.init_db()


from src.utils.users import get_current_user
# Для вебсокетов:
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db_for_websockets)):
    await websocket.accept()
    user = await db.execute(select(User).filter(User.id == 1))
    user = user.scalars().first()
    await websocket.send_text(f"Hello, {user.nickname}!")
    await websocket.close()







from src.utils.users import hash_password, verify_password, create_access_token

from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from src.db.models import User, UserCreate, disease_symptoms, DiseaseUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(db: AsyncSession, email: str, password: str, nickname: str):
    # Проверка, существует ли уже пользователь с таким email
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if user:
        return None  # Если пользователь существует

    password_hash = pwd_context.hash(password)
    new_user = User(email=email, password_hash=password_hash, nickname=nickname)

    db.add(new_user)
    await db.commit()
    return new_user





from pydantic import EmailStr
from src.db.models import UserLogin


@app.post("/register", tags=['Пользователи'])
async def register_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    # Проверяем, существует ли пользователь с таким email
    result = await session.execute(select(User).filter(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Проверяем, существует ли пользователь с таким nickname
    result = await session.execute(select(User).filter(User.nickname == user.nickname))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Nickname already taken")

    # Хешируем пароль
    hashed_password = hash_password(user.password)

    # Создаем нового пользователя
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        nickname=user.nickname,
        age=user.age  # Добавляем возраст
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return {
        "msg": "User created",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "nickname": db_user.nickname,
            "age": db_user.age
        }
    }


from pydantic import BaseModel
from typing import Optional


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    age: Optional[int] = None


from pydantic import BaseModel
from typing import Optional


@app.put("/user/update", tags=['Пользователи'])
async def update_user(
        user_data: UserUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить данные пользователя"""
    try:
        if user_data.nickname:
            # Проверяем уникальность никнейма
            result = await db.execute(select(User).filter(User.nickname == user_data.nickname))
            if result.scalars().first() and result.scalars().first().id != current_user.id:
                raise HTTPException(status_code=400, detail="Nickname already taken")
            current_user.nickname = user_data.nickname

        if user_data.age is not None:
            current_user.age = user_data.age

        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)

        return {
            "msg": "User updated",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "nickname": current_user.nickname,
                "age": current_user.age
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/login", tags=['Пользователи'])
async def login_user(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_data.email))
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "nickname": user.nickname,
        "email": user.email
    }

from src.db.models import AllUsersProfilesMain
from src.utils.users import get_current_user
from src.utils.users import get_users
@app.get("/allusers", response_model=list[AllUsersProfilesMain], tags=['Пользователи'])
async def get_all_users(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),):
    """Список всех пользователей, доступен всем"""
    offset = offset * limit
    users = await get_users(sessionmanager.session(), limit, offset)
    return users


@app.get("/user_info/{user_id}", tags=['Пользователи'])
async def get_user_info(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/user_info_by_nickname/{nickname}", tags=['Пользователи'])
async def get_user_info_by_nickname(nickname: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.nickname == nickname))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user



from src.utils.users import NoteCreate, NoteResponse
from src.utils.users import create_note, get_notes_by_user
from src.utils.users import get_current_user  # Функция для получения текущего пользователя


@app.post("/add_note", response_model=NoteResponse, tags=['Заметки'])
async def add_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Добавить новую заметку"""
    return await create_note(db, current_user.id, note_data)


from src.db.models import UserResponse

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.utils.users import Note, NoteResponse


@app.get("/notes", response_model=list[NoteResponse], tags=['Заметки'])
async def get_user_notes(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),  # Исправлено
):
    """Получить все заметки пользователя"""
    result = await db.execute(
        select(Note)
        .filter(Note.user_id == current_user.id)  # Теперь точно User, а не dict
    )
    notes = result.scalars().all()

    if not notes:
        return []  # Если заметок нет, возвращаем пустой список

    return notes  # Возвращаем список заметок


@app.put("/edit_note/{note_id}", tags=['Заметки'])
async def edit_note(
    note_id: int,
    new_text: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Редактировать заметку пользователя по ID"""
    try:
        # Поиск заметки
        note = await db.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Заметка не найдена")

        # Проверка владельца заметки
        if note.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Вы не можете редактировать чужую заметку")

        # Обновление текста заметки
        note.text = new_text
        db.add(note)

        # Коммит изменений
        await db.commit()
        await db.refresh(note)

        return {"message": "Заметка обновлена", "note": {"id": note.id, "text": note.text}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/delete_note/{note_id}", tags=['Заметки'])
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить заметку пользователя по ID"""
    try:
        # Поиск заметки
        note = await db.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Заметка не найдена")

        # Проверка владельца заметки
        if note.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Вы не можете удалить чужую заметку")

        # Удаление заметки
        await db.delete(note)
        await db.commit()

        return {"message": "Заметка удалена"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





from src.utils.users import add_disease_to_user, get_user_diseases  # Импортируем функции

from sqlalchemy.future import select

from sqlalchemy.future import select

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

@app.post("/add_disease/{disease_id}", tags=['Болезни'])
async def add_disease(
    disease_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Добавить болезнь в список пользователя"""
    try:
        # 1. Загружаем болезнь через асинхронный запрос
        result = await db.execute(select(Disease).where(Disease.id == disease_id))
        disease = result.scalars().first()

        if not disease:
            raise HTTPException(status_code=404, detail="Болезнь не найдена")

        # 2. Загружаем пользователя вместе с болезнями
        user_result = await db.execute(
            select(User).options(selectinload(User.diseases)).where(User.id == current_user.id)
        )
        user = user_result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # 3. Проверяем, есть ли болезнь у пользователя
        if disease in user.diseases:
            raise HTTPException(status_code=400, detail="Болезнь уже добавлена пользователю")

        # 4. Добавляем болезнь в список пользователя
        user.diseases.append(disease)
        db.add(user)

        # 5. Синхронизируем данные
        await db.commit()
        await db.refresh(user)

        return {"message": "Болезнь добавлена", "disease": disease.name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/disease/{disease_id}/update", response_model=dict, tags=['Болезни'])
async def update_disease(
    disease_id: int,
    disease_data: DiseaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Находим болезнь
    disease = await db.get(Disease, disease_id)
    if not disease:
        raise HTTPException(status_code=404, detail="Болезнь не найдена")

    # Обновляем поля, если они переданы
    if disease_data.name:
        result = await db.execute(select(Disease).filter(Disease.name == disease_data.name))
        existing_disease = result.scalars().first()
        if existing_disease and existing_disease.id != disease_id:
            raise HTTPException(status_code=400, detail="Болезнь с таким названием уже существует")
        disease.name = disease_data.name

    if disease_data.description is not None:
        disease.description = disease_data.description
    if disease_data.age_min is not None:
        disease.age_min = disease_data.age_min
    if disease_data.age_max is not None:
        disease.age_max = disease_data.age_max

    db.add(disease)
    await db.commit()
    await db.refresh(disease)

    return {"msg": "Disease updated", "id": disease.id, "name": disease.name}


@app.get("/diseases", response_model=list[str], tags=['Болезни'])
async def get_diseases(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Получить список болезней пользователя"""
    return await get_user_diseases(db, current_user["id"])


from src.db.models import Disease
from src.db.models import DiseaseCreate


@app.post("/disease", response_model=dict, tags=['Болезни'])
async def create_disease(disease_data: DiseaseCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Disease).filter(Disease.name == disease_data.name))
    existing_disease = result.scalars().first()

    if existing_disease:
        raise HTTPException(status_code=400, detail="Болезнь с таким названием уже существует")

    new_disease = Disease(
        name=disease_data.name,
        description=disease_data.description,
        age_min=disease_data.age_min,
        age_max=disease_data.age_max
    )
    db.add(new_disease)
    await db.commit()
    await db.refresh(new_disease)

    return {"msg": "Disease created", "id": new_disease.id, "name": new_disease.name}


"""Симптомы--------------------------------------"""
from src.utils.users import create_symptom, link_disease_symptom
from src.db.models import Symptom, DiseaseSymptomLink,SymptomResponse,SymptomCreate

@app.post("/symptom", response_model=SymptomResponse, tags=['Симптомы'])
async def add_symptom(symptom_data: SymptomCreate, db: AsyncSession = Depends(get_db)):
    """Добавить новый симптом"""
    return await create_symptom(db, symptom_data.name)

@app.post("/disease/{disease_id}/add_symptom/{symptom_id}", tags=['Симптомы'])
async def add_symptom_to_disease(
    disease_id: int,
    symptom_id: int,
    weight: float = 1.0,  # Опционально, по умолчанию 1.0
    db: AsyncSession = Depends(get_db)
):
    """Привязать симптом к болезни с указанием веса"""
    try:
        # Проверяем существование болезни и симптома
        disease = await db.get(Disease, disease_id)
        symptom = await db.get(Symptom, symptom_id)
        if not disease or not symptom:
            raise HTTPException(status_code=404, detail="Болезнь или симптом не найдены")

        # Проверяем, нет ли уже такой связи
        result = await db.execute(
            select(disease_symptoms).filter_by(disease_id=disease_id, symptom_id=symptom_id)
        )
        if result.first():
            raise HTTPException(status_code=400, detail="Симптом уже привязан к болезни")

        # Добавляем связь с указанным весом
        await db.execute(
            disease_symptoms.insert().values(
                disease_id=disease_id,
                symptom_id=symptom_id,
                weight=weight
            )
        )
        await db.commit()

        return {
            "msg": "Симптом привязан к болезни",
            "disease_id": disease_id,
            "symptom_id": symptom_id,
            "weight": weight
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/user_diseases", tags=['Болезни'])
async def get_user_diseases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список болезней пользователя (название и описание)"""
    try:
        await db.refresh(current_user, ["diseases"])  # Обновляем данные пользователя
        diseases = current_user.diseases  # Получаем список болезней

        return [
            {"name": disease.name, "description": disease.description}
            for disease in diseases
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models import Disease
from src.db.database import get_db
from src.utils.users import  get_current_user


from sqlalchemy.orm import selectinload

from sqlalchemy.orm import selectinload

@app.post("/predict_disease", tags=['Вспомогательные функции'])
async def predict_disease(
    symptoms: list[str],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Предсказание болезней с учетом симптомов (основной фактор), их весов и минимального влияния возраста"""
    try:
        # Получаем пользователя для проверки возраста
        user = await db.get(User, current_user.id)
        if user.age is None:
            raise HTTPException(status_code=400, detail="Возраст пользователя не указан")

        # Получаем все болезни с их симптомами
        result = await db.execute(
            select(Disease).options(selectinload(Disease.symptoms))
        )
        diseases = result.scalars().all()

        if not diseases:
            raise HTTPException(status_code=404, detail="Болезни не найдены")

        disease_probabilities = []

        for disease in diseases:
            # Получаем веса симптомов из таблицы disease_symptoms
            symptom_weights = await db.execute(
                select(disease_symptoms.c.weight)
                .filter(disease_symptoms.c.disease_id == disease.id)
                .join(Symptom, Symptom.id == disease_symptoms.c.symptom_id)
            )
            weights = [row[0] for row in symptom_weights]

            # Сумма весов всех симптомов болезни
            total_weight = sum(weights) if weights else 1.0

            # Сумма весов совпадающих симптомов
            matched_weight = 0.0
            for symptom in disease.symptoms:
                if symptom.name in symptoms:
                    result = await db.execute(
                        select(disease_symptoms.c.weight)
                        .filter(
                            disease_symptoms.c.disease_id == disease.id,
                            disease_symptoms.c.symptom_id == symptom.id
                        )
                    )
                    weight = result.scalar_one_or_none() or 1.0
                    matched_weight += weight

            if matched_weight > 0:
                # Базовая вероятность на основе симптомов (0-100%)
                symptom_probability = (matched_weight / total_weight) * 100

                # Корректировка на возраст с учётом age_min и age_max
                age_adjustment = 0.0
                if disease.age_min is not None and user.age < disease.age_min:
                    age_adjustment = -10.0  # Уменьшаем вероятность на 10%, если возраст меньше минимального
                elif disease.age_max is not None and user.age > disease.age_max:
                    age_adjustment = -10.0  # Уменьшаем вероятность на 10%, если возраст больше максимального
                else:
                    age_adjustment = 5.0  # Увеличиваем на 5%, если возраст в диапазоне

                # Дополнительная корректировка для крайних возрастных групп
                if user.age < 18:
                    age_adjustment -= 5.0  # Ещё -5% для детей
                elif user.age > 60:
                    age_adjustment += 5.0  # Ещё +5% для пожилых

                # Итоговая вероятность с учетом возраста
                final_probability = symptom_probability + age_adjustment
                # Ограничиваем вероятность диапазоном 0-100
                final_probability = max(0.0, min(100.0, final_probability))

                disease_probabilities.append({
                    "disease": disease.name,
                    "probability": round(final_probability, 2)
                })

        # Сортируем по убыванию вероятности
        disease_probabilities.sort(key=lambda x: x["probability"], reverse=True)

        # Возвращаем топ-3 результата
        return {"predictions": disease_probabilities[:3]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/remove_disease/{disease_id}", tags=['Болезни'])
async def remove_disease(
    disease_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить болезнь из списка пользователя"""
    try:
        # Загружаем пользователя с его болезнями
        user_result = await db.execute(
            select(User).options(selectinload(User.diseases)).where(User.id == current_user.id)
        )
        user = user_result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Проверяем, есть ли болезнь у пользователя
        disease_to_remove = next((d for d in user.diseases if d.id == disease_id), None)

        if not disease_to_remove:
            raise HTTPException(status_code=400, detail="Болезнь отсутствует у пользователя")

        # Удаляем болезнь из списка
        user.diseases.remove(disease_to_remove)
        db.add(user)

        # Сохраняем изменения
        await db.commit()
        await db.refresh(user)

        return {"message": "Болезнь удалена", "disease": disease_to_remove.name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





from src.db.models import HealthMetric
from src.db.models  import HealthMetricCreate, HealthMetricResponse

@app.post("/add_health_metric", response_model=HealthMetricResponse, tags=["Здоровье"])
async def add_health_metric(
    metric: HealthMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Добавить новый показатель здоровья"""
    new_metric = HealthMetric(user_id=current_user.id, name=metric.name, value=metric.value)
    db.add(new_metric)
    await db.commit()
    await db.refresh(new_metric)
    return new_metric

@app.get("/health_metrics", response_model=list[HealthMetricResponse], tags=["Здоровье"])
async def get_health_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить все показатели здоровья пользователя"""
    result = await db.execute(select(HealthMetric).filter(HealthMetric.user_id == current_user.id))
    metrics = result.scalars().all()
    return metrics