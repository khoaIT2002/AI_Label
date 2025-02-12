import os
class Settings:

    DATABASE_URL = os.environ.get('DATABASE_URL','postgresql://postgres:newcomer7952@localhost:5432/test_fastapi')
    SECRET_KEY = os.environ.get('SECRET_KEY','SERECT_KEY')
    ALGORITHM = os.environ.get('ALGORITHM','HS256')

settings = Settings()   