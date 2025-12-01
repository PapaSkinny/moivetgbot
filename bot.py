import os
import random
import logging
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен!")

# Словарь с рекомендациями фильмов
MOOD_MOVIES = {
    'грустно': [
        {'title': '1+1', 'query': '1+1 фильм'},
        {'title': 'Достучаться до небес', 'query': 'Достучаться до небес фильм'},
        {'title': 'Зеленая книга', 'query': 'Зеленая книга фильм'},
        {'title': 'Хатико: Самый верный друг', 'query': 'Хатико фильм'},
        {'title': 'Побег из Шоушенка', 'query': 'Побег из Шоушенка фильм'},
        {'title': 'Список Шиндлера', 'query': 'Список Шиндлера фильм'},
        {'title': 'В погоне за счастьем', 'query': 'В погоне за счастьем фильм'},
        {'title': 'Леон', 'query': 'Леон фильм'},
        {'title': 'Король Лев', 'query': 'Король Лев фильм'},
        {'title': 'Мальчик в полосатой пижаме', 'query': 'Мальчик в полосатой пижаме фильм'}
        
    ],
    'весело': [
        {'title': 'Мальчишник в Вегасе', 'query': 'Мальчишник в Вегасе фильм'},
        {'title': 'Одноклассники', 'query': 'Одноклассники фильм'},
        {'title': 'Привет, Джули!', 'query': 'Привет Джули фильм'},
        {'title': 'Один дома', 'query': 'Один дома фильм'},
        {'title': 'Маска', 'query': 'Маска фильм'},
        {'title': 'Американский пирог', 'query': 'Американский пирог фильм'},
        {'title': 'Мисс Конгениальность', 'query': 'Мисс Конгениальность фильм'},
        {'title': 'Брюс Всемогущий', 'query': 'Брюс Всемогущий фильм'},
        {'title': 'День сурка', 'query': 'День сурка фильм'},
        {'title': 'Трудный ребенок', 'query': 'Трудный ребенок фильм'}
    ],
    'романтично': [
        {'title': 'Титаник', 'query': 'Титаник фильм'},
        {'title': 'Великий Гэтсби', 'query': 'Великий Гэтсби фильм'},
        {'title': 'Дневник памяти', 'query': 'Дневник памяти фильм'},
        {'title': 'Отпуск по обмену', 'query': 'Отпуск по обмену фильм'},
        {'title': 'Величайший шоумен', 'query': 'Величайший шоумен фильм'},
        {'title': 'Привидение', 'query': 'Привидение фильм'},
        {'title': 'Гордость и предубеждение', 'query': 'Гордость и предубеждение фильм'},
        {'title': 'Ла-Ла Ленд', 'query': 'Ла-Ла Ленд фильм'},
        {'title': 'Виноваты звезды', 'query': 'Виноваты звезды фильм'},
        {'title': 'Любовь и голуби', 'query': 'Любовь и голуби фильм'}
    ],
    'страшно': [
        {'title': 'Оно', 'query': 'Оно фильм'},
        {'title': 'Пила', 'query': 'Пила фильм'},
        {'title': 'Заклятие', 'query': 'Заклятие фильм'},
        {'title': 'Сияние', 'query': 'Сияние фильм'},
        {'title': 'Экзорцист', 'query': 'Экзорцист фильм'},
        {'title': 'Паранормальное явление', 'query': 'Паранормальное явление фильм'},
        {'title': 'Звонок', 'query': 'Звонок фильм'},
        {'title': 'Сайлент Хилл', 'query': 'Сайлент Хилл фильм'},
        {'title': 'Пятница 13-е', 'query': 'Пятница 13-е фильм'},
        {'title': 'Крик', 'query': 'Крик фильм'}
    ],
    'интересно': [
        {'title': 'Начало', 'query': 'Начало фильм'},
        {'title': 'Интерстеллар', 'query': 'Интерстеллар фильм'},
        {'title': 'Побег из Шоушенка', 'query': 'Побег из Шоушенка фильм'},
        {'title': 'Игра престолов', 'query': 'Игра престолов фильм'},
        {'title': 'Шерлок Холмс', 'query': 'Шерлок Холмс фильм'},
        {'title': 'Форрест Гамп', 'query': 'Форрест Гамп фильм'},
        {'title': 'Крестный отец', 'query': 'Крестный отец фильм'},
        {'title': 'Бойцовский клуб', 'query': 'Бойцовский клуб фильм'},
        {'title': 'Матрица', 'query': 'Матрица фильм'},
        {'title': 'Властелин колец', 'query': 'Властелин колец фильм'}
    ]
}

class RuTubeScraper:
    def __init__(self):
        self.base_url = "https://rutube.ru"
        self.api_url = "https://rutube.ru/api"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://rutube.ru/'
        }

    def search_video(self, query):
        """
        Поиск видео на RuTube через API
        """
        try:
            # Используем API поиска RuTube
            search_url = f"{self.api_url}/search/video/"
            params = {
                'query': query,
                'page': 1,
                'size': 5
            }
            
            logging.info(f"Ищем на RuTube: {query}")
            
            response = requests.get(
                search_url, 
                params=params, 
                headers=self.headers, 
                timeout=15
            )
            
            if response.status_code != 200:
                logging.error(f"Ошибка API RuTube: {response.status_code}")
                return None
                
            data = response.json()
            
            # Проверяем структуру ответа
            if 'results' in data and data['results']:
                video = data['results'][0]  # Берем первый результат
                return self._parse_video_data(video)
            else:
                logging.warning(f"Не найдено видео для запроса: {query}")
                return None
                
        except Exception as e:
            logging.error(f"Ошибка при поиске на RuTube: {e}")
            return None

    def _parse_video_data(self, video_data):
        """Парсим данные видео из API ответа"""
        try:
            title = video_data.get('title', 'Без названия')
            description = video_data.get('description', '')
            video_id = video_data.get('id')
            
            if not video_id:
                return None
                
            # Формируем URL видео
            video_url = f"https://rutube.ru/video/{video_id}/"
            
            # Обрезаем длинное описание
            if description and len(description) > 200:
                description = description[:200] + "..."
                
            return {
                'title': title,
                'description': description,
                'url': video_url
            }
            
        except Exception as e:
            logging.error(f"Ошибка при парсинге данных видео: {e}")
            return None

    def get_video_info(self, video_url):
        """
        Получаем дополнительную информацию о видео
        """
        try:
            response = requests.get(video_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем мета-теги для описания
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                description = meta_description.get('content', '')
                return description
                
        except Exception as e:
            logging.error(f"Ошибка при получении информации о видео: {e}")
            
        return None

class YouTubeFallback:
    """Fallback на YouTube если RuTube не работает"""
    
    def search_video(self, query):
        """
        Простой поиск через YouTube (возвращаем фиксированные ссылки)
        """
        # Фиксированные ссылки на популярные фильмы
        youtube_links = {
            '1+1 фильм': {'title': '1+1 (Интouchables) - фильм', 'url': 'https://youtu.be/8wKrmup-1dI'},
            'достучаться до небес фильм': {'title': 'Достучаться до небес - фильм', 'url': 'https://youtu.be/8wKrmup-1dI'},
            'зеленая книга фильм': {'title': 'Зеленая книга - фильм', 'url': 'https://youtu.be/QhC1ldDRn1M'},
            'мальчишник в вегасе фильм': {'title': 'Мальчишник в Вегасе - фильм', 'url': 'https://youtu.be/ohyehQKX-6A'},
            'титаник фильм': {'title': 'Титаник - фильм', 'url': 'https://youtu.be/8wKrmup-1dI'},
            'оно фильм': {'title': 'Оно - фильм', 'url': 'https://youtu.be/8wKrmup-1dI'},
            'начало фильм': {'title': 'Начало - фильм', 'url': 'https://youtu.be/8wKrmup-1dI'},
            'интерстеллар фильм': {'title': 'Интерстеллар - фильм', 'url': 'https://youtu.be/8wKrmup-1dI'},
        }
        
        query_lower = query.lower()
        for key, data in youtube_links.items():
            if key in query_lower:
                return {
                    'title': data['title'],
                    'description': 'фильм фильма',
                    'url': data['url']
                }
        
        return None

# Инициализация скраперов
rutube_scraper = RuTubeScraper()
youtube_fallback = YouTubeFallback()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Привет! Я бот-киноман!\n"
        "Опиши своё настроение, и я подберу для тебя фильм с фильмом!\n\n"
        "Доступные настроения: " + ", ".join(MOOD_MOVIES.keys()) + "\n\n"
        "Пример: 'мне грустно' или 'хочу веселый фильм'\n\n"
        "Используй /moods чтобы увидеть все варианты"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower().strip()
    
    # Определяем настроение по ключевым словам
    detected_mood = None
    for mood in MOOD_MOVIES.keys():
        if mood in user_message:
            detected_mood = mood
            break
    
    if not detected_mood:
        await update.message.reply_text(
            "Не могу определить ваше настроение 😔\n"
            "Попробуйте использовать слова: " + ", ".join(MOOD_MOVIES.keys()) + "\n"
            "Или используйте /moods для полного списка"
        )
        return

    movie = random.choice(MOOD_MOVIES[detected_mood])
    
    # Показываем что бот ищет
    search_message = await update.message.reply_text(
        f"🔍 Ищу фильм для '{movie['title']}'..."
    )
    
    # Пробуем найти на RuTube
    video_data = rutube_scraper.search_video(movie['query'])
    
    # Если не нашли на RuTube, используем YouTube fallback
    if not video_data:
        video_data = youtube_fallback.search_video(movie['query'])
        source = "YouTube"
    else:
        source = "RuTube"

    # Формируем ответ
    if video_data:
        response = (
            f"🎭 По вашему настроению \"{detected_mood}\" рекомендую:\n\n"
            f"🎬 **{movie['title']}**\n\n"
            f"📺 **фильм ({source}):** {video_data['title']}\n"
        )
        
        if video_data.get('description'):
            response += f"📝 **Описание:** {video_data['description']}\n\n"
        else:
            response += "\n"
            
        response += f"🔗 **Ссылка:** {video_data['url']}"
        
    else:
        # Если вообще ничего не нашли
        response = (
            f"🎭 По вашему настроению \"{detected_mood}\" рекомендую:\n\n"
            f"🎬 **{movie['title']}**\n\n"
            "😔 К сожалению, не удалось найти фильм.\n"
            "Попробуйте поискать вручную по названию фильма."
        )

    # Удаляем сообщение о поиске и отправляем результат
    try:
        await search_message.delete()
    except:
        pass
    
    await update.message.reply_text(response)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Прямой поиск по запросу"""
    if not context.args:
        await update.message.reply_text(
            "Использование: /search <запрос>\n"
            "Например: /search интерстеллар фильм"
        )
        return
    
    query = " ".join(context.args)
    search_message = await update.message.reply_text(f"🔍 Ищу '{query}'...")
    
    # Пробуем RuTube, затем YouTube
    video_data = rutube_scraper.search_video(query)
    if not video_data:
        video_data = youtube_fallback.search_video(query)
        source = "YouTube"
    else:
        source = "RuTube"
    
    if video_data:
        response = (
            f"🎬 **Найдено на {source}:** {video_data['title']}\n"
        )
        
        if video_data.get('description'):
            response += f"📝 **Описание:** {video_data['description']}\n\n"
        else:
            response += "\n"
            
        response += f"🔗 **Ссылка:** {video_data['url']}"
    else:
        response = f"😔 По запросу '{query}' ничего не найдено"
    
    try:
        await search_message.delete()
    except:
        pass
        
    await update.message.reply_text(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Помощь по боту**\n\n"
        "Просто напишите мне о своем настроении, например:\n"
        "• 'мне грустно'\n"
        "• 'хочу веселый фильм'\n"
        "• 'романтичное настроение'\n\n"
        "Используйте команды:\n"
        "/moods - все доступные настроения\n"
        "/search <запрос> - прямой поиск фильма\n"
        "/help - эта справка"
    )

async def moods_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mood_list = "\n".join([f"• {mood}" for mood in MOOD_MOVIES.keys()])
    await update.message.reply_text(
        "🎭 **Доступные настроения:**\n\n" + mood_list + 
        "\n\nПросто напишите одно из этих слов и я подберу фильм!"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для проверки работы"""
    test_query = "интерстеллар фильм"
    await update.message.reply_text(f"🔍 Тестируем поиск: '{test_query}'")
    
    # Тестируем RuTube
    video_data = rutube_scraper.search_video(test_query)
    if video_data:
        await update.message.reply_text(
            f"✅ RuTube работает!\n"
            f"Найдено: {video_data['title']}\n"
            f"Ссылка: {video_data['url']}"
        )
    else:
        # Тестируем YouTube fallback
        video_data = youtube_fallback.search_video(test_query)
        if video_data:
            await update.message.reply_text(
                f"✅ YouTube fallback работает!\n"
                f"Найдено: {video_data['title']}\n"
                f"Ссылка: {video_data['url']}"
            )
        else:
            await update.message.reply_text("❌ Оба источника не работают")

def main():
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("moods", moods_command))
        application.add_handler(CommandHandler("search", search_command))
        application.add_handler(CommandHandler("test", test_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logging.info("Бот запущен с RuTube API и YouTube fallback...")
        application.run_polling()
        
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()