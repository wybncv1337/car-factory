"""Генератор тестовых данных с известными фактами"""

import random
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.file_utils import write_text_file, ensure_folder

class TestDataGenerator:
    def __init__(self):
        self.companies = ["АвтоВАЗ", "Toyota", "BMW", "Hyundai", "Kia", "Volkswagen", "Ford", "Tesla"]
        self.positions = ["инженер-конструктор", "программист Python", "менеджер проекта", "директор по развитию", "специалист по тестированию", "системный аналитик"]
        self.products = ["новую модель электромобиля", "внедорожник", "спортивный седан", "кроссовер", "хэтчбек", "минивэн"]
    
    def generate_vacancy_text(self):
        company = random.choice(self.companies)
        position = random.choice(self.positions)
        salary = random.randint(50, 250) * 1000
        exp = random.randint(1, 7)
        schedule = random.choice(["полный день", "удалённо", "гибкий график"])
        
        templates = [
            f"Компания {company} открывает вакансию {position}. Зарплата от {salary} рублей. Опыт работы от {exp} лет. График: {schedule}.",
            f"Требуется {position}. Условия: зарплата {salary} руб, опыт {exp} года, график {schedule}. Откликайтесь!",
            f"Ищем {position} в команду {company}. Предлагаем: оклад {salary} руб, опыт от {exp} лет."
        ]
        return random.choice(templates)
    
    def generate_price_text(self):
        product = random.choice(self.products)
        price = random.randint(1, 5) * 1000000
        
        templates = [
            f"Новый {product} по цене {price} рублей. Успейте купить!",
            f"Специальное предложение! {product} всего {price} ₽.",
            f"Цена на {product} снижена до {price} руб. Скидка действует до конца месяца."
        ]
        return random.choice(templates)
    
    def generate_release_text(self):
        company = random.choice(self.companies)
        product = random.choice(self.products)
        date = f"{random.randint(1,28)}.{random.randint(1,12)}.2026"
        
        templates = [
            f"Компания {company} выпустила {product}. Релиз состоялся {date}.",
            f"Презентация {product} от {company} прошла успешно. Старт продаж {date}.",
            f"Анонс! {company} представляет {product}. Официальный релиз запланирован на {date}."
        ]
        return random.choice(templates)
    
    def generate_fact_text(self):
        r = random.random()
        if r < 0.33:
            return self.generate_vacancy_text()
        elif r < 0.66:
            return self.generate_price_text()
        else:
            return self.generate_release_text()
    
    def generate_noise_text(self, i):
        templates = [
            f"Обычный текст номер {i}. Сегодня хорошая погода. Завтра будет лучше.",
            f"Страница {i} ни о чём. Просто какой-то контент для заполнения места.",
            f"Это тестовый файл {i}. Он не содержит полезной информации."
        ]
        return random.choice(templates)
    
    def generate_dataset(self, num_files=100, fact_ratio=0.33):
        ensure_folder('data/test')
        
        num_fact_files = int(num_files * fact_ratio)
        print(f"📊 Генерация {num_files} тестовых файлов: {num_fact_files} с фактами")
        
        fact_count = 0
        for i in range(num_files):
            if i < num_fact_files:
                if random.random() < 0.2:
                    text = self.generate_fact_text() + "\n\n" + self.generate_fact_text()
                    fact_count += 2
                else:
                    text = self.generate_fact_text()
                    fact_count += 1
            else:
                text = self.generate_noise_text(i)
            
            write_text_file(f"data/test/doc_{i:03d}.txt", text)
        
        print(f"✅ Сгенерировано фактов: {fact_count}")
        return fact_count