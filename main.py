from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette.websockets import WebSocket
from src.db.database import sessionmanager, get_db, get_db_for_websockets
from src.db.models import (
    User, Disease, Symptom, Note, HealthMetric,
    UserCreate, UserResponse, UserLogin, AllUsersProfilesMain,
    DiseaseCreate, DiseaseResponse, SymptomCreate, SymptomResponse,
    DiseaseSymptomLink,
    HealthMetricCreate, HealthMetricResponse, PredictionRequest, PredictionResponse, disease_symptoms
)
from src.utils.users import (
    hash_password, verify_password, create_access_token, get_user_by_nickname,
    get_users, get_current_user, create_note, get_notes_by_user,NoteCreate, NoteResponse,
    add_disease_to_user, get_user_diseases, create_symptom, link_disease_symptom
)

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    sessionmanager.init_db()

# Для вебсокетов
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db_for_websockets)):
    await websocket.accept()
    user = await db.execute(select(User).filter(User.id == 1))
    user = user.scalars().first()
    await websocket.send_text(f"Hello, {user.nickname}!")
    await websocket.close()

# Регистрация пользователя
@app.post("/register", tags=['Пользователи'])
async def register_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).filter(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await session.execute(select(User).filter(User.nickname == user.nickname))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Nickname already taken")

    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        nickname=user.nickname,
        age=user.age
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

# Обновление данных пользователя
class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    age: Optional[int] = None

@app.put("/user/update", tags=['Пользователи'])
async def update_user(
        user_data: UserUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if user_data.nickname:
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

# Вход пользователя
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

# Получение списка всех пользователей
@app.get("/allusers", response_model=list[AllUsersProfilesMain], tags=['Пользователи'])
async def get_all_users(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    offset = offset * limit
    users = await get_users(sessionmanager.session(), limit, offset)
    return users

# Получение информации о пользователе по ID
@app.get("/user_info/{user_id}", tags=['Пользователи'])
async def get_user_info(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Получение информации о пользователе по никнейму
@app.get("/user_info_by_nickname/{nickname}", tags=['Пользователи'])
async def get_user_info_by_nickname(nickname: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.nickname == nickname))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Добавление заметки
@app.post("/add_note", response_model=NoteResponse, tags=['Заметки'])
async def add_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_note(db, current_user.id, note_data)

# Получение заметок пользователя
@app.get("/notes", response_model=list[NoteResponse], tags=['Заметки'])
async def get_user_notes(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Note).filter(Note.user_id == current_user.id)
    )
    notes = result.scalars().all()
    if not notes:
        return []
    return notes

# Редактирование заметки
@app.put("/edit_note/{note_id}", tags=['Заметки'])
async def edit_note(
    note_id: int,
    new_text: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = await db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не можете редактировать чужую заметку")
    note.text = new_text
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return {"message": "Заметка обновлена", "note": {"id": note.id, "text": note.text}}

# Удаление заметки
@app.delete("/delete_note/{note_id}", tags=['Заметки'])
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = await db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не можете удалить чужую заметку")
    await db.delete(note)
    await db.commit()
    return {"message": "Заметка удалена"}

# Добавление болезни пользователю
@app.post("/add_disease/{disease_id}", tags=['Болезни'])
async def add_disease(
    disease_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Disease).where(Disease.id == disease_id))
    disease = result.scalars().first()
    if not disease:
        raise HTTPException(status_code=404, detail="Болезнь не найдена")

    user_result = await db.execute(
        select(User).options(selectinload(User.diseases)).where(User.id == current_user.id)
    )
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if disease in user.diseases:
        raise HTTPException(status_code=400, detail="Болезнь уже добавлена пользователю")

    user.diseases.append(disease)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "Болезнь добавлена", "disease": disease.name}

# Получение списка болезней пользователя
@app.get("/diseases", response_model=list[str], tags=['Болезни'])
async def get_diseases(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await get_user_diseases(db, current_user.id)

# Создание болезни (без токена)
@app.post("/disease", response_model=DiseaseResponse, tags=['Болезни'])
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
    return new_disease

# Добавление симптома
@app.post("/symptom", response_model=SymptomResponse, tags=['Симптомы'])
async def add_symptom(symptom_data: SymptomCreate, db: AsyncSession = Depends(get_db)):
    return await create_symptom(db, symptom_data.name)

# Привязка симптома к болезни с весом
@app.post("/disease/{disease_id}/add_symptom/{symptom_id}", tags=['Симптомы'])
async def add_symptom_to_disease(
    disease_id: int,
    symptom_id: int,
    link_data: DiseaseSymptomLink,
    db: AsyncSession = Depends(get_db)
):
    disease = await db.get(Disease, disease_id)
    symptom = await db.get(Symptom, symptom_id)
    if not disease or not symptom:
        raise HTTPException(status_code=404, detail="Болезнь или симптом не найдены")

    result = await db.execute(
        select(disease_symptoms).filter_by(disease_id=disease_id, symptom_id=symptom_id)
    )
    if result.first():
        raise HTTPException(status_code=400, detail="Симптом уже привязан к болезни")

    await db.execute(
        disease_symptoms.insert().values(
            disease_id=disease_id,
            symptom_id=symptom_id,
            weight=link_data.weight
        )
    )
    await db.commit()
    return {
        "msg": "Симптом привязан к болезни",
        "disease_id": disease_id,
        "symptom_id": symptom_id,
        "weight": link_data.weight
    }

# Получение списка болезней пользователя (с описанием)
@app.get("/user/user_diseases", tags=['Болезни'])
async def get_user_diseases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await db.refresh(current_user, ["diseases"])
    diseases = current_user.diseases
    return [
        {"name": disease.name, "description": disease.description}
        for disease in diseases
    ]

# Предсказание болезни
@app.post("/predict_disease", response_model=PredictionResponse, tags=['Вспомогательные функции'])
async def predict_disease(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Получаем возраст пользователя
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

    # Получаем все симптомы
    result = await db.execute(select(Symptom))
    all_symptoms = result.scalars().all()
    if not all_symptoms:
        raise HTTPException(status_code=404, detail="Симптомы не найдены")

    # Находим ID симптомов, которые пользователь отправил
    symptom_names = request.symptom_names
    symptom_ids = []
    for name in symptom_names:
        symptom = next((s for s in all_symptoms if s.name == name), None)
        if symptom:
            symptom_ids.append(symptom.id)
        else:
            raise HTTPException(status_code=400, detail=f"Симптом '{name}' не найден")

    if not symptom_ids:
        raise HTTPException(status_code=400, detail="Не предоставлено ни одного валидного симптома")

    # Вычисляем вероятности для каждой болезни
    predictions = []
    for disease in diseases:
        # Получаем все симптомы, связанные с этой болезнью
        disease_symptoms = [(ds.disease_id, ds.symptom_id, ds.weight) for ds in disease.symptoms]

        # Суммируем веса симптомов, которые есть у пользователя
        total_weight = sum(ds[2] for ds in disease_symptoms)  # Сумма всех весов симптомов болезни
        matched_weight = sum(
            ds[2] for ds in disease_symptoms
            if ds[1] in symptom_ids  # symptom_id совпадает
        )

        if matched_weight > 0:
            # Базовая вероятность на основе симптомов
            symptom_probability = (matched_weight / total_weight) * 100

            # Применяем возрастной коэффициент
            age_coefficient = 1.0
            if disease.age_min is not None and disease.age_max is not None:
                if disease.age_min <= user.age <= disease.age_max:
                    age_coefficient = 1.05  # +5%
                else:
                    age_coefficient = 0.95  # -5%

            adjusted_probability = symptom_probability * age_coefficient
            adjusted_probability = min(adjusted_probability, 100.0)

            predictions.append({
                "disease": disease.name,
                "description": disease.description,
                "probability": round(adjusted_probability, 2)
            })

    # Сортируем по убыванию вероятности
    predictions.sort(key=lambda x: x["probability"], reverse=True)

    # Возвращаем топ-5 результатов
    return {"predictions": predictions[:5]}

# Удаление болезни из списка пользователя
@app.delete("/remove_disease/{disease_id}", tags=['Болезни'])
async def remove_disease(
    disease_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_result = await db.execute(
        select(User).options(selectinload(User.diseases)).where(User.id == current_user.id)
    )
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    disease_to_remove = next((d for d in user.diseases if d.id == disease_id), None)
    if not disease_to_remove:
        raise HTTPException(status_code=400, detail="Болезнь отсутствует у пользователя")

    user.diseases.remove(disease_to_remove)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "Болезнь удалена", "disease": disease_to_remove.name}

# Добавление показателя здоровья
@app.post("/add_health_metric", response_model=HealthMetricResponse, tags=["Здоровье"])
async def add_health_metric(
    metric: HealthMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_metric = HealthMetric(user_id=current_user.id, name=metric.name, value=metric.value)
    db.add(new_metric)
    await db.commit()
    await db.refresh(new_metric)
    return new_metric

# Получение показателей здоровья
@app.get("/health_metrics", response_model=list[HealthMetricResponse], tags=["Здоровье"])
async def get_health_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(HealthMetric).filter(HealthMetric.user_id == current_user.id))
    metrics = result.scalars().all()
    return metrics

# Получение списка всех симптомов
@app.get("/symptoms", response_model=list[SymptomResponse], tags=['Симптомы'])
async def get_symptoms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Symptom))
    symptoms = result.scalars().all()
    if not symptoms:
        return []
    return symptoms