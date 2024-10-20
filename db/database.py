from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import check_password_hash
import certifi
import streamlit as st

DEFAULT_SETTINGS = {
    "ace_theme": "twilight",
    "ace_font_size": 14,
    "language": "markdown",
    "show_gutter": True,
    "node_color": "#34ebd8",
    "edge_color": "#eb34eb",
    "directed": True,
    "edge_curve": "bezier",
    "layout": 'cose'
}


# Функция для подключения к MongoDB Atlas
@st.cache_resource
def get_db(uri, db_name):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        db = client[db_name]
        # Проверяем соединение
        client.admin.command('ping')
        return db
    except ConnectionFailure:
        st.error("Не удалось подключиться к серверу")
        return None

# Подключение к базе данных
db_password = st.secrets["mongo"]["password"]  # Достаем пароль из секретов
db_name = st.secrets["mongo"]["name"]  # Название базы данных
db_username = st.secrets["mongo"]["username"]

# Строка подключения к MongoDB Atlas
uri = f"mongodb+srv://{db_username}:{db_password}@braingrokker.a6uqrlj.mongodb.net/?retryWrites=true&w=majority&appName=BrainGrokker"

# Получаем базу данных
db = get_db(uri=uri, db_name=db_name)

# Проверяем успешность подключения
if db is not None:
    st.success("Успешно подключено к базе данных")



def register_user(login, password_hash):
    user = {
        "login": login,
        "password_hash": password_hash,
        "reg_time": datetime.now(),
        "settings": DEFAULT_SETTINGS
    }
    result = db['users'].insert_one(user)
    return str(result.inserted_id)


def authenticate_user(login, password):
    # Найти пользователя по email
    user = db['users'].find_one({"login": login})
    if user:
        # Проверить пароль
        if check_password_hash(user['password_hash'], password):
            return str(user['_id'])  # Возвращаем ID пользователя при успешной аутентификации
    return None  # Возвращаем None, если аутентификация не удалась


def get_user_by_id(user_id):
    return db['users'].find_one({"_id": ObjectId(user_id)})

def get_user_by_login(login):
    return db['users'].find_one({"login": login})



# Функции для работы с заметками

def create_note(user_id, title, summary, content, tags=None, links=None): #user_id, title, summary, content, color, tags=None, links=None
    note = {
        "content": content,
        "title": title,
        "summary": summary,
        "tags": tags if tags else [],
        "links": links if links else [],
        "user_id": ObjectId(user_id),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    result = db['notes'].insert_one(note)
    return str(result.inserted_id)

def get_notes_by_id(note_id):
    return db['notes'].find({"_id": ObjectId(note_id)})

def get_notes_by_user_id(user_id):
    notes = db['notes'].find({"user_id": ObjectId(user_id)}, {'title': 1, '_id': 1})
    return {note['title']: note['_id'] for note in notes}


def update_note(note_id, content=None, tags=None, links=None):
    update_data = {"updated_at": datetime.now()}
    if content:
        update_data["content"] = content
    if tags is not None:
        update_data["tags"] = tags
    if links is not None:
        update_data["links"] = links

    result = db['notes'].update_one(
        {"_id": ObjectId(note_id)},
        {"$set": update_data}
    )
    return result.modified_count

def delete_note(note_id):
    result = db['notes'].delete_one({"_id": ObjectId(note_id)})
    return result.deleted_count


def get_all_tags(user_id):
    tags = db['tags'].find({"user_id": ObjectId(user_id)}, {'tag_name': 1, '_id': 1})
    return {tag['tag_name']: tag['_id'] for tag in tags}

def add_tag(tag_name, user_id):
    result = db['tags'].insert_one({'user_id': ObjectId(user_id), 'tag_name': tag_name})
    return str(result.inserted_id)


def get_readable_note_details(note_id):
    pipeline = [
        {
            "$match": {
                "_id": ObjectId(note_id)  # ID вашей заметки
            }
        },
        {
            "$lookup": {
                "from": "tags",
                "localField": "tags",
                "foreignField": "_id",
                "as": "tag_details"
            }
        },
        {
            "$lookup": {
                "from": "notes",
                "localField": "links",
                "foreignField": "_id",
                "as": "link_details"
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "summary": 1,
                "content": 1,
                "tags": "$tag_details.tag_name",  # Извлечение названий тегов
                "links": "$link_details.title",  # Извлечение названий ссылок
                "user_id": 1,
                "created_at": 1,
                "updated_at": 1
            }
        }
    ]

    result = list(db['notes'].aggregate(pipeline))
    
    if result:
        return result[0]  # Вернуть первый (и единственный) результат
    else:
        return None  # Если ничего не найдено

# ---
def get_notes_with_tags(user_id, tags):
    if not tags:
        return list(db['notes'].find({"user_id": ObjectId(user_id)}))
    tag_ids = [ObjectId(tag_id) for tag_id in tags]
    return list(db['notes'].find({"user_id": ObjectId(user_id), "tags": {"$in": tag_ids}}))

def get_links_for_notes(note_ids):
    note_ids = [ObjectId(note_id) for note_id in note_ids]
    return list(db['notes'].find({"_id": {"$in": note_ids}}, {"links": 1}))

def get_tag_name_by_id(tag_id):
    tag = db['tags'].find_one({"_id": ObjectId(tag_id)}, {"tag_name": 1})
    return tag['tag_name'] if tag else None


def load_user_settings(user_id):
    user = get_user_by_id(user_id)
    settings = user.get('settings', DEFAULT_SETTINGS)
    return settings

def save_user_settings(user_id, settings):
    db['users'].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"settings": settings}}
    )


def get_notes_data(user_id):
    """
    Возвращает данные заметок пользователя, включая время создания и другую информацию
    """
    notes = db['notes'].find(
        {"user_id": ObjectId(user_id)},
        {"title": 1, "created_at": 1, "summary": 1, "tags": 1, "links": 1}
    )
    return list(notes)