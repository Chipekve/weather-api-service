from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

PAGE_SIZE = 3
TEXT_SET_CITY = "поменять что-то в жизни"
TEXT_WEATHER = "👀 Чо по погоде?"
TEXT_SHOW_CITY = "чо по городу 🤌🏻"
CANCEL_TEXT = "❌Отмена"
CANCEL_KB = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=CANCEL_TEXT, callback_data="cancel_city")]
    ]
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=TEXT_WEATHER)],
        [KeyboardButton(text=TEXT_SHOW_CITY), KeyboardButton(text=TEXT_SET_CITY)],
        [KeyboardButton(text="Популярные города")]
    ],
    resize_keyboard=True
)

POPULAR_CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград"
]
POPULAR_PAGE = 5

SHOW_IMAGE_TEXT = "🖼️ Показать картинкой"
SHOW_IMAGE_CALLBACK = "show_image"

def get_cities_keyboard(cities, has_next, page, query):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{city['name']}, {city.get('country', '')}".strip(', '),
                callback_data=f"city_{city['id']}_{page}_{query}")]
            for city in cities
        ] +
        ([[InlineKeyboardButton(text="◀️ Назад", callback_data=f"page_{page-1}_{query}")]] if page > 1 else []) +
        ([[InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"page_{page+1}_{query}")]] if has_next else [])
    )
    return kb

def get_popular_cities_keyboard(page=1):
    start = (page - 1) * POPULAR_PAGE
    end = start + POPULAR_PAGE
    cities = POPULAR_CITIES[start:end]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=city, callback_data=f"popularcity_{city}"),
                InlineKeyboardButton(text="Прогноз на 3 дня", callback_data=f"popularforecast_{city}")
            ]
            for city in cities
        ]
    )
    # Пагинация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"popularpage_{page-1}"))
    if end < len(POPULAR_CITIES):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"popularpage_{page+1}"))
    if nav_buttons:
        kb.inline_keyboard.append(nav_buttons)
    return kb

def get_weather_image_keyboard(city=None):
    if city:
        callback_data = f"{SHOW_IMAGE_CALLBACK}:{city}"
    else:
        callback_data = SHOW_IMAGE_CALLBACK
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=SHOW_IMAGE_TEXT, callback_data=callback_data)]
        ]
    ) 