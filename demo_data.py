"""Демонстрационная витрина AI News: 78 событий, неравномерно разложенных по 60 дням."""

DEMO_SEED_VERSION = "4"

# Официальные сайты компаний-разработчиков: нужны для кнопки «Сайт компании» на карточках.
DEVELOPER_SITES = {
    "OpenAI": "https://openai.com",
    "Anthropic": "https://www.anthropic.com",
    "Google": "https://about.google",
    "Microsoft": "https://www.microsoft.com",
    "AWS": "https://aws.amazon.com",
    "Meta": "https://about.meta.com",
    "Adobe": "https://www.adobe.com",
    "Canva": "https://www.canva.com",
    "Figma": "https://www.figma.com",
    "GitHub": "https://github.com",
    "Hugging Face": "https://huggingface.co",
    "Mistral AI": "https://mistral.ai",
    "Perplexity": "https://www.perplexity.ai",
    "Runway": "https://runwayml.com",
    "ElevenLabs": "https://elevenlabs.io",
    "Grammarly": "https://www.grammarly.com",
    "Notion": "https://www.notion.so",
    "Zoom": "https://www.zoom.com",
    "Яндекс": "https://yandex.ru",
    "Сбер": "https://www.sberbank.com",
}

# Страницы новостей компаний: кнопка «Читать новость». URL взяты из sources.csv,
# где источник уже подключён к сборщику; для остальных — официальные пресс-страницы.
DEVELOPER_NEWS_PAGES = {
    "OpenAI": "https://openai.com/news/",
    "Anthropic": "https://www.anthropic.com/news",
    "Google": "https://blog.google/technology/ai/",
    "Microsoft": "https://blogs.microsoft.com/blog/tag/ai/",
    "AWS": "https://aws.amazon.com/about-aws/whats-new/",
    "Meta": "https://about.fb.com/news/",
    "Adobe": "https://blog.adobe.com/en/topics/ai",
    "Canva": "https://www.canva.com/newsroom/",
    "Figma": "https://www.figma.com/blog/",
    "GitHub": "https://github.blog/category/ai/",
    "Hugging Face": "https://huggingface.co/blog",
    "Mistral AI": "https://mistral.ai/news/",
    "Perplexity": "https://www.perplexity.ai/hub",
    "Runway": "https://runwayml.com/news/",
    "ElevenLabs": "https://elevenlabs.io/blog",
    "Grammarly": "https://www.grammarly.com/blog/",
    "Notion": "https://www.notion.so/blog",
    "Zoom": "https://www.zoom.com/en/blog/",
    "Яндекс": "https://yandex.ru/company/press_releases/",
    "Сбер": "https://developers.sber.ru/portal/products/gigachat",
}

# Сколько событий пришлось на каждый из 60 дней: затишье (0) чередуется со
# всплесками (2-3), поэтому график читается как новостной поток, а не ровная линейка.
DAILY_COUNTS = [
    3, 2, 1, 1, 2, 1, 3, 1, 2, 1,
    2, 1, 0, 3, 1, 2, 1, 1, 3, 1,
    1, 2, 1, 1, 1, 0, 2, 1, 1, 2,
    1, 1, 1, 0, 3, 1, 2, 1, 1, 0,
    2, 1, 1, 2, 1, 1, 1, 2, 1, 1,
    1, 0, 1, 1, 1, 2, 1, 1, 1, 1,
]


def day_schedule(event_count):
    """Раскрывает DAILY_COUNTS в «сколько дней назад» для каждого события."""
    days = [days_ago for days_ago, count in enumerate(DAILY_COUNTS) for _ in range(count)]
    if len(days) < event_count:
        days += [len(DAILY_COUNTS) - 1] * (event_count - len(days))
    return days[:event_count]


# type, данные карточки, страница источника
_EVENTS = [
    # OpenAI
    ("tool", {"name": "ChatGPT", "developer": "OpenAI", "category": "Текст и анализ", "description": "ИИ-ассистент для текста, анализа документов и рабочих задач.", "price": "Есть бесплатный тариф", "value": "ChatGPT — ИИ-помощник для рабочих задач."}, "https://chatgpt.com"),
    ("update", {"name": "Работа с файлами в ChatGPT", "developer": "OpenAI", "category": "Текст и анализ", "description": "Обновление помощника: загрузка документов и разбор длинных текстов.", "value": "OpenAI: обновления ChatGPT для работы с документами."}, "https://openai.com/chatgpt/overview/"),
    ("pricing", {"name": "Тарифы ChatGPT", "developer": "OpenAI", "category": "Текст и анализ", "description": "Сведения о доступных планах и лимитах сервиса.", "price": "Есть бесплатный тариф", "value": "OpenAI: тарифы и лимиты ChatGPT."}, "https://chatgpt.com/pricing"),
    ("update", {"name": "Обновления моделей в API", "developer": "OpenAI", "category": "Разработка", "description": "Новые версии моделей и режимы рассуждения для разработчиков.", "value": "OpenAI: обновления моделей в API."}, "https://openai.com/news/"),
    # Anthropic
    ("tool", {"name": "Claude", "developer": "Anthropic", "category": "Текст и анализ", "description": "Ассистент для работы с большими текстами, кодом и документами.", "price": "Есть бесплатный тариф", "value": "Claude — ИИ-ассистент от Anthropic."}, "https://claude.ai"),
    ("update", {"name": "Проектные пространства Claude", "developer": "Anthropic", "category": "Текст и анализ", "description": "Обновление: совместная работа над задачами и общие знания проекта.", "value": "Anthropic: проектные функции Claude."}, "https://www.anthropic.com/news"),
    ("pricing", {"name": "Планы Claude", "developer": "Anthropic", "category": "Текст и анализ", "description": "Информация о бесплатном доступе и платных подписках.", "price": "Есть бесплатный тариф", "value": "Anthropic: планы доступа Claude."}, "https://www.anthropic.com/pricing"),
    ("tool", {"name": "Claude Code", "developer": "Anthropic", "category": "Разработка", "description": "Агент в терминале: читает репозиторий, правит код и запускает тесты.", "price": "Платная подписка", "value": "Claude Code — ИИ-агент для работы с кодом."}, "https://www.anthropic.com/news"),
    # Google
    ("tool", {"name": "Gemini", "developer": "Google", "category": "Текст и мультимедиа", "description": "Мультимодальный ИИ-помощник для задач с текстом и изображениями.", "price": "Есть бесплатный тариф", "value": "Gemini — ИИ-помощник от Google."}, "https://gemini.google.com"),
    ("update", {"name": "ИИ в Google Workspace", "developer": "Google", "category": "Продуктивность", "description": "Обновления помощника в Почте, Документах и Таблицах.", "value": "Google: ИИ-функции в Workspace."}, "https://workspace.google.com/products/gemini/"),
    ("pricing", {"name": "Подписка Google AI", "developer": "Google", "category": "Текст и мультимедиа", "description": "Условия платных планов и объём хранилища в комплекте.", "price": "Платная подписка", "value": "Google: платные ИИ-планы."}, "https://one.google.com/about/google-ai-plans/"),
    ("update", {"name": "ИИ-режим в поиске", "developer": "Google", "category": "Поиск и анализ", "description": "Обновление поиска: сводка по запросу и уточняющие вопросы.", "value": "Google: ИИ-режим в поиске."}, "https://blog.google/technology/ai/"),
    # Microsoft
    ("tool", {"name": "Microsoft Copilot", "developer": "Microsoft", "category": "Продуктивность", "description": "Помощник для рабочих задач и приложений Microsoft.", "price": "Зависит от тарифа Microsoft 365", "value": "Microsoft Copilot — ИИ-помощник для работы."}, "https://copilot.microsoft.com"),
    ("update", {"name": "Copilot в Microsoft 365", "developer": "Microsoft", "category": "Продуктивность", "description": "Обновления помощника в Word, Excel и Teams.", "value": "Microsoft: обновления Copilot для продуктивности."}, "https://www.microsoft.com/microsoft-365/copilot"),
    ("pricing", {"name": "Copilot для организаций", "developer": "Microsoft", "category": "Продуктивность", "description": "Отдельные условия для частных пользователей и организаций.", "price": "Зависит от тарифа Microsoft 365", "value": "Microsoft: тарифы Copilot."}, "https://www.microsoft.com/en-us/microsoft-365/copilot-for-microsoft-365-business-plans"),
    ("tool", {"name": "Azure AI Foundry", "developer": "Microsoft", "category": "Разработка", "description": "Среда для сборки ИИ-приложений и агентов на разных моделях.", "price": "Оплата по мере использования", "value": "Azure AI Foundry — платформа ИИ-приложений."}, "https://blogs.microsoft.com/blog/tag/ai/"),
    # AWS
    ("tool", {"name": "Amazon Q Developer", "developer": "AWS", "category": "Разработка", "description": "ИИ-помощник для разработки, отладки и работы с инфраструктурой.", "price": "Есть бесплатный тариф", "value": "Amazon Q Developer — помощник для разработчиков."}, "https://aws.amazon.com/q/developer/"),
    ("update", {"name": "Агенты в Amazon Bedrock", "developer": "AWS", "category": "Разработка", "description": "Обновление платформы: автономные агенты и подключение к данным.", "value": "AWS: агентские функции Bedrock."}, "https://aws.amazon.com/bedrock/"),
    ("pricing", {"name": "Оплата Amazon Bedrock", "developer": "AWS", "category": "Разработка", "description": "Плата за использование моделей по объёму запросов.", "price": "Оплата по мере использования", "value": "AWS: модель оплаты Bedrock."}, "https://aws.amazon.com/bedrock/pricing/"),
    ("tool", {"name": "Amazon Titan", "developer": "AWS", "category": "Исследования", "description": "Собственные модели AWS для текста, изображений и поисковых сценариев.", "price": "Оплата по мере использования", "value": "Amazon Titan — облачные ИИ-модели."}, "https://aws.amazon.com/about-aws/whats-new/"),
    # Meta
    ("tool", {"name": "Meta AI", "developer": "Meta", "category": "Текст и мультимедиа", "description": "Помощник на открытых моделях Llama внутри приложений Meta.", "price": "Бесплатно в приложениях Meta", "value": "Meta AI — ассистент в мессенджерах."}, "https://www.meta.ai"),
    ("update", {"name": "Открытые модели Llama", "developer": "Meta", "category": "Исследования", "description": "Новые версии моделей для текстовых и визуальных задач.", "value": "Meta: обновления открытых моделей Llama."}, "https://www.llama.com"),
    ("pricing", {"name": "Условия Meta AI", "developer": "Meta", "category": "Текст и мультимедиа", "description": "Доступ к помощнику зависит от приложения и региона.", "price": "Есть бесплатный доступ", "value": "Meta: условия доступа Meta AI."}, "https://www.meta.ai/help"),
    ("update", {"name": "Лицензия открытых моделей", "developer": "Meta", "category": "Исследования", "description": "Обновление условий: как компаниям использовать модели в своих продуктах.", "value": "Meta: лицензия открытых моделей."}, "https://about.fb.com/news/"),
    # Adobe
    ("tool", {"name": "Adobe Firefly", "developer": "Adobe", "category": "Дизайн", "description": "Генеративные модели для изображений, эффектов и видео.", "price": "Входит в подписку Adobe", "value": "Adobe Firefly — генеративный ИИ для дизайна."}, "https://www.adobe.com/products/firefly.html"),
    ("update", {"name": "Генеративное заполнение", "developer": "Adobe", "category": "Дизайн", "description": "Обновление Photoshop: расширение фона и точечное редактирование.", "value": "Adobe: генеративные функции Photoshop."}, "https://www.adobe.com/products/photoshop/generative-fill.html"),
    ("pricing", {"name": "Кредиты генерации", "developer": "Adobe", "category": "Дизайн", "description": "Генеративные функции работают по системе кредитов.", "price": "Зависит от количества кредитов", "value": "Adobe: кредиты для генеративных функций."}, "https://www.adobe.com/creativecloud/plans.html"),
    ("tool", {"name": "Adobe Express", "developer": "Adobe", "category": "Дизайн", "description": "Быстрый дизайн постов и презентаций с ИИ-подсказками.", "price": "Есть бесплатный тариф", "value": "Adobe Express — ИИ для простого дизайна."}, "https://blog.adobe.com/en/topics/ai"),
    # Canva
    ("tool", {"name": "Canva Magic Studio", "developer": "Canva", "category": "Дизайн", "description": "Набор ИИ-инструментов для макетов, презентаций и текста.", "price": "Есть бесплатный тариф", "value": "Canva Magic Studio — ИИ для дизайна."}, "https://www.canva.com/magic-studio/"),
    ("update", {"name": "ИИ-редактирование видео", "developer": "Canva", "category": "Дизайн", "description": "Обновление: монтаж и субтитры с помощью ИИ.", "value": "Canva: ИИ-функции для видео."}, "https://www.canva.com/video-editor/"),
    ("pricing", {"name": "Тарифы Canva", "developer": "Canva", "category": "Дизайн", "description": "Информация о тарифах и доступе к ИИ-функциям.", "price": "Есть бесплатный тариф", "value": "Canva: тарифы и ИИ-функции."}, "https://www.canva.com/pricing/"),
    ("update", {"name": "Перевод макетов", "developer": "Canva", "category": "Дизайн", "description": "Обновление: перевод текста на макетах и автомасштабирование под форматы.", "value": "Canva: мультиязычные макеты."}, "https://www.canva.com/newsroom/"),
    # Figma
    ("tool", {"name": "Figma AI", "developer": "Figma", "category": "Дизайн", "description": "ИИ-функции для макетов, переименования слоёв и поиска по дизайну.", "price": "Зависит от тарифа Figma", "value": "Figma AI — ИИ для проектирования интерфейсов."}, "https://www.figma.com/ai/"),
    ("update", {"name": "First Draft и Make", "developer": "Figma", "category": "Дизайн", "description": "Обновление: генерация черновых макетов и кода по описанию.", "value": "Figma: генеративные инструменты для макетов."}, "https://www.figma.com/blog/"),
    ("pricing", {"name": "Планы Figma", "developer": "Figma", "category": "Дизайн", "description": "Доступ к планам и их ИИ-возможностям.", "price": "Зависит от выбранного тарифа", "value": "Figma: планы и ИИ-функции."}, "https://www.figma.com/pricing/"),
    ("tool", {"name": "Figma Slides", "developer": "Figma", "category": "Дизайн", "description": "Презентации внутри Figma с ИИ-помощником для текста и макетов.", "price": "Зависит от тарифа Figma", "value": "Figma Slides — презентации в Figma."}, "https://www.figma.com/blog/"),
    # GitHub
    ("tool", {"name": "GitHub Copilot", "developer": "GitHub", "category": "Разработка", "description": "Подсказывает код, объясняет ошибки и помогает в ревью.", "price": "Платный, есть пробный период", "value": "GitHub Copilot — ИИ-помощник для кода."}, "https://github.com/features/copilot"),
    ("update", {"name": "Copilot Workspace", "developer": "GitHub", "category": "Разработка", "description": "Обновление: задачи от описания до pull request в одной среде.", "value": "GitHub: Copilot Workspace для задач."}, "https://github.blog/category/ai/"),
    ("pricing", {"name": "Тарифы Copilot", "developer": "GitHub", "category": "Разработка", "description": "Отдельные планы для частного использования, команд и предприятий.", "price": "Есть несколько тарифов", "value": "GitHub Copilot: планы и условия."}, "https://github.com/features/copilot/plans"),
    ("tool", {"name": "GitHub Models", "developer": "GitHub", "category": "Разработка", "description": "Каталог ИИ-моделей с песочницей и сравнением ответов.", "price": "Входит в подписку GitHub Copilot", "value": "GitHub Models — каталог ИИ-моделей."}, "https://github.blog/category/ai/"),
    # Hugging Face
    ("tool", {"name": "Hugging Face Hub", "developer": "Hugging Face", "category": "Разработка", "description": "Платформа с открытыми моделями, датасетами и демо.", "price": "Есть бесплатные возможности", "value": "Hugging Face — платформа для ИИ-моделей."}, "https://huggingface.co"),
    ("update", {"name": "Inference Endpoints", "developer": "Hugging Face", "category": "Разработка", "description": "Обновление сервиса развёртывания моделей в изолированной среде.", "value": "Hugging Face: развёртывание моделей."}, "https://huggingface.co/blog"),
    ("pricing", {"name": "Подписки PRO и ENTERPRISE", "developer": "Hugging Face", "category": "Разработка", "description": "Платные планы дают приватные репозитории и приоритетные квоты.", "price": "Есть бесплатный тариф", "value": "Hugging Face: планы подписки."}, "https://huggingface.co/pricing"),
    ("update", {"name": "Открытые датасеты", "developer": "Hugging Face", "category": "Исследования", "description": "Обновление карточек моделей и наборов данных для обучения.", "value": "Hugging Face: обновления датасетов."}, "https://huggingface.co/blog"),
    # Mistral AI
    ("tool", {"name": "Le Chat", "developer": "Mistral AI", "category": "Текст и анализ", "description": "Чат-ассистент для повседневных задач и работы с текстом.", "price": "Есть бесплатный тариф", "value": "Le Chat — ИИ-ассистент от Mistral AI."}, "https://chat.mistral.ai"),
    ("update", {"name": "Открытые модели Mistral", "developer": "Mistral AI", "category": "Исследования", "description": "Новые версии моделей для локального запуска и тонкой настройки.", "value": "Mistral AI: обновления открытых моделей."}, "https://mistral.ai/news/"),
    ("pricing", {"name": "Тарифы Mistral AI", "developer": "Mistral AI", "category": "Текст и анализ", "description": "Информация о доступе к чату и API по объёму запросов.", "price": "Есть бесплатный тариф", "value": "Mistral AI: тарифы и доступ к Le Chat."}, "https://mistral.ai/pricing/"),
    ("tool", {"name": "Mistral API", "developer": "Mistral AI", "category": "Разработка", "description": "Доступ к моделям для чатов, классификации и агентов.", "price": "Оплата по мере использования", "value": "Mistral AI: API для разработчиков."}, "https://mistral.ai/news/"),
    # Perplexity
    ("tool", {"name": "Perplexity", "developer": "Perplexity", "category": "Поиск и анализ", "description": "Поисковый ИИ-сервис с ответами и ссылками на источники.", "price": "Есть бесплатный тариф", "value": "Perplexity — ИИ-поиск с источниками."}, "https://www.perplexity.ai"),
    ("update", {"name": "Deep Research", "developer": "Perplexity", "category": "Поиск и анализ", "description": "Обновление: многошаговый поиск с отчётом и списком источников.", "value": "Perplexity: режим глубокого исследования."}, "https://www.perplexity.ai/hub"),
    ("pricing", {"name": "Планы Perplexity", "developer": "Perplexity", "category": "Поиск и анализ", "description": "Информация о бесплатном и расширенном доступе.", "price": "Есть бесплатный тариф", "value": "Perplexity: планы и возможности."}, "https://www.perplexity.ai/pro"),
    ("tool", {"name": "Perplexity Pages", "developer": "Perplexity", "category": "Поиск и анализ", "description": "ИИ собирает отчёт по запросу в отдельную страницу с источниками.", "price": "Есть бесплатный тариф", "value": "Perplexity Pages — отчёты по запросу."}, "https://www.perplexity.ai/hub"),
    # Runway
    ("tool", {"name": "Runway", "developer": "Runway", "category": "Видео", "description": "ИИ-инструмент для генерации и монтажа видео.", "price": "Есть бесплатный тариф", "value": "Runway — ИИ-инструмент для видео."}, "https://runwayml.com"),
    ("update", {"name": "Генерация видео по тексту", "developer": "Runway", "category": "Видео", "description": "Обновление моделей: более длинные клипы и управление камерой.", "value": "Runway: обновления генерации видео."}, "https://runwayml.com/research"),
    ("pricing", {"name": "Кредиты Runway", "developer": "Runway", "category": "Видео", "description": "Генерация расходует кредиты, их объём зависит от плана.", "price": "Платная подписка", "value": "Runway: тарифы и кредиты."}, "https://runwayml.com/pricing"),
    ("update", {"name": "Монтаж по текстовому описанию", "developer": "Runway", "category": "Видео", "description": "Обновление: правки клипа и удаление фона по подсказке.", "value": "Runway: ИИ-монтаж видео."}, "https://runwayml.com/news/"),
    # ElevenLabs
    ("tool", {"name": "ElevenLabs Voice", "developer": "ElevenLabs", "category": "Аудио", "description": "Синтез речи, клонирование голоса и озвучка материалов.", "price": "Есть бесплатный тариф", "value": "ElevenLabs — ИИ-генерация голоса."}, "https://elevenlabs.io"),
    ("update", {"name": "Мультиязычная озвучка", "developer": "ElevenLabs", "category": "Аудио", "description": "Обновление: дубляж с сохранением тембра голоса на других языках.", "value": "ElevenLabs: функции дубляжа."}, "https://elevenlabs.io/blog"),
    ("pricing", {"name": "Тарифы ElevenLabs", "developer": "ElevenLabs", "category": "Аудио", "description": "Сведения о лимитах символов и доступных планах.", "price": "Есть бесплатный тариф", "value": "ElevenLabs: тарифы и лимиты."}, "https://elevenlabs.io/pricing"),
    ("update", {"name": "Студия продакшн озвучки", "developer": "ElevenLabs", "category": "Аудио", "description": "Обновление: проекты с несколькими дорожками, эффектами и дубляжом.", "value": "ElevenLabs: студия для озвучки."}, "https://elevenlabs.io/blog"),
    # Grammarly
    ("tool", {"name": "Grammarly", "developer": "Grammarly", "category": "Текст", "description": "Проверка и улучшение англоязычных текстов, писем и документов.", "price": "Есть бесплатный тариф", "value": "Grammarly — ИИ-помощник для текста."}, "https://www.grammarly.com"),
    ("update", {"name": "Стили и тон письма", "developer": "Grammarly", "category": "Текст", "description": "Обновление: переписывание фрагментов под нужный тон и аудиторию.", "value": "Grammarly: управление тоном текста."}, "https://www.grammarly.com/blog/"),
    ("pricing", {"name": "Планы Grammarly", "developer": "Grammarly", "category": "Текст", "description": "Бесплатная проверка и расширенные функции в платных планах.", "price": "Есть бесплатный тариф", "value": "Grammarly: планы подписки."}, "https://www.grammarly.com/plans"),
    # Notion
    ("tool", {"name": "Notion AI", "developer": "Notion", "category": "Продуктивность", "description": "Помощник внутри рабочих пространств: конспекты, тексты, базы знаний.", "price": "Платная подписка", "value": "Notion AI — ассистент в рабочих пространствах."}, "https://www.notion.so/product/ai"),
    ("update", {"name": "Агенты и базы знаний", "developer": "Notion", "category": "Продуктивность", "description": "Обновление: агенты собирают ответы из внутренних страниц и задач.", "value": "Notion: агенты для рабочих пространств."}, "https://www.notion.so/blog"),
    ("pricing", {"name": "Лимиты Notion AI", "developer": "Notion", "category": "Продуктивность", "description": "Объём ИИ-запросов зависит от выбранного тарифа.", "price": "Зависит от тарифа", "value": "Notion: лимиты ИИ-функций в тарифах."}, "https://www.notion.so/pricing"),
    ("tool", {"name": "Notion AI Connector", "developer": "Notion", "category": "Продуктивность", "description": "Коннектор к корпоративным сервисам: помощник отвечает по данным из Slack и Drive.", "price": "Платная подписка", "value": "Notion AI Connector — ИИ по внешним данным."}, "https://www.notion.so/blog"),
    # Zoom
    ("tool", {"name": "Zoom AI Companion", "developer": "Zoom", "category": "Встречи", "description": "Помощник для встреч: резюме разговора, задачи и документы.", "price": "Входит в платные тарифы", "value": "Zoom AI Companion — ИИ для встреч."}, "https://www.zoom.com/en/products/ai-assistant/"),
    ("update", {"name": "Субтитры и перевод", "developer": "Zoom", "category": "Встречи", "description": "Обновление: ИИ-субтитры и перевод разговора в реальном времени.", "value": "Zoom: ИИ-субтитры на встречах."}, "https://www.zoom.com/en/blog/"),
    ("pricing", {"name": "Тарифы Zoom", "developer": "Zoom", "category": "Встречи", "description": "Часть ИИ-функций доступна только на платных планах.", "price": "Есть бесплатный тариф", "value": "Zoom: тарифы и доступ к ИИ."}, "https://www.zoom.com/en/pricing/"),
    # Яндекс
    ("tool", {"name": "YandexGPT", "developer": "Яндекс", "category": "Текст и анализ", "description": "Русскоязычная языковая модель для генерации и обработки текста.", "price": "Условия зависят от сервиса", "value": "YandexGPT — русскоязычная ИИ-модель."}, "https://yandex.ru/project/yandexgpt"),
    ("update", {"name": "ИИ в Яндекс Облаке", "developer": "Яндекс", "category": "Разработка", "description": "Обновление платформы для разработчиков и бизнеса.", "value": "Яндекс: ИИ-инструменты для разработчиков."}, "https://yandex.cloud/ru/services/yandexgpt"),
    ("pricing", {"name": "Доступ к YandexGPT", "developer": "Яндекс", "category": "Текст и анализ", "description": "Условия использования различаются для сервисов и API.", "price": "Условия зависят от сервиса", "value": "Яндекс: доступ к YandexGPT."}, "https://yandex.ru/company/press_releases/"),
    ("tool", {"name": "Алиса AI", "developer": "Яндекс", "category": "Текст и мультимедиа", "description": "Помощник в устройствах и сервисах Яндекса: ответы, тексты, изображения.", "price": "Есть бесплатный доступ", "value": "Алиса AI — голосовой помощник Яндекса."}, "https://yandex.ru/company/press_releases/"),
    # Сбер
    ("tool", {"name": "GigaChat", "developer": "Сбер", "category": "Текст и анализ", "description": "Российский ИИ-ассистент для общения, текста и рабочих задач.", "price": "Условия зависят от сервиса", "value": "GigaChat — ИИ-ассистент от Сбера."}, "https://developers.sber.ru/portal/products/gigachat"),
    ("update", {"name": "GigaChat API", "developer": "Сбер", "category": "Разработка", "description": "Обновление API для интеграций и генерации ответов в приложениях.", "value": "Сбер: обновление GigaChat API."}, "https://developers.sber.ru/portal/products/gigachat"),
    ("pricing", {"name": "Тарифы GigaChat", "developer": "Сбер", "category": "Текст и анализ", "description": "Информация о вариантах доступа и лимитах для разработчиков.", "price": "Условия зависят от сервиса", "value": "Сбер: тарифы GigaChat."}, "https://developers.sber.ru/portal/products/gigachat"),
    ("update", {"name": "GigaChat для бизнеса", "developer": "Сбер", "category": "Продуктивность", "description": "Обновление: корпоративные знания и готовые сценарии в ассистенте.", "value": "Сбер: GigaChat для компаний."}, "https://developers.sber.ru/portal/products/gigachat"),
]

# type, данные карточки, страница источника, сколько дней назад произошло
DEMO_FACTS = [(*event, days_ago) for event, days_ago in zip(_EVENTS, day_schedule(len(_EVENTS)))]
