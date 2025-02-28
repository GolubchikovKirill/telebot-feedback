from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from .models import Base

load_dotenv()
DB_URL = os.getenv("DB_URL")

class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def create_session(self):
        """Создаёт сессию для работы с базой данных, которая поддерживает контекстный менеджер"""
        return self.Session()  # Возвращаем сам объект сессии

    def commit(self):
        """Подтверждает изменения в базе данных"""
        if self.session:
            self.session.commit()

    def close(self):
        """Закрывает сессию"""
        if self.session:
            self.session.close()

    def create_all(self):
        """Создает все таблицы в базе данных"""
        Base.metadata.create_all(self.engine)

# Инициализация базы данных
db = Database(DB_URL)
db.create_all()  # Создаем все таблицы