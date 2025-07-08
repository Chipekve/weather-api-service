from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import logging


def generate_weather_image(weather_data, city):
    width, height = 500, 300
    # Трёхцветный градиент: лаванда (#e0c3fc) -> светло-розовый (#f9e4ff) -> тёплый белый (#fffbe9)
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    top_color = (224, 195, 252)    # #e0c3fc
    middle_color = (249, 228, 255)  # #f9e4ff
    bottom_color = (255, 251, 233)  # #fffbe9
    for y in range(height):
        if y < height // 2:
            ratio = y / (height // 2)
            r = int(top_color[0] * (1 - ratio) + middle_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + middle_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + middle_color[2] * ratio)
        else:
            ratio = (y - height // 2) / (height // 2)
            r = int(middle_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(middle_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(middle_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    font_path = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")
    try:
        font_city = ImageFont.truetype(font_path, 28)
        font_temp = ImageFont.truetype(font_path, 44)
        font_cond = ImageFont.truetype(font_path, 24)
        font_date = ImageFont.truetype(font_path, 18)
    except Exception as e:
        logging.warning(
            f"Не удалось загрузить шрифт {font_path}: {e}. Используется стандартный шрифт (английский, без кириллицы)"
        )
        font_city = font_temp = font_cond = font_date = ImageFont.load_default()

    temp = weather_data['current']['temp_c']
    condition = weather_data['current']['condition']['text']
    date = weather_data['location']['localtime'].split()[0]

    # Эмодзи по погоде
    cond_lower = condition.lower()
    if "дожд" in cond_lower:
        emoji = "🌧️"
    elif "ясно" in cond_lower or "солнечно" in cond_lower:
        emoji = "☀️"
    elif "обла" in cond_lower:
        emoji = "☁️"
    elif "снег" in cond_lower:
        emoji = "❄️"
    elif "туман" in cond_lower:
        emoji = "🌫️"
    elif "гроза" in cond_lower:
        emoji = "🌩️"
    else:
        emoji = "🌤️"

    # Тень для читаемости
    def draw_embossed_text(x, y, text, font, fill, highlight="#ffffff", shadow="#222222", offset=2):
        # Светлый контур (сверху/слева)
        draw.text((x-offset, y-offset), text, font=font, fill=highlight)
        # Тёмный контур (снизу/справа)
        draw.text((x+offset, y+offset), text, font=font, fill=shadow)
        # Основной текст
        draw.text((x, y), text, font=font, fill=fill)

    # Город (реальное название)
    draw_embossed_text(30, 28, city, font_city, fill="#222222", highlight="#ffffff", shadow="#888888", offset=2)
    # Температура
    draw_embossed_text(30, 80, f"{temp}°C", font_temp, fill="#333333", highlight="#ffffff", shadow="#888888", offset=2)
    # Эмодзи и состояние
    draw_embossed_text(
        30, 150, f"{emoji}  {condition}", font_cond, fill="#444444", highlight="#ffffff", shadow="#888888", offset=1
    )
    # Дата
    draw_embossed_text(
        width-140, height-40, date, font_date, fill="#888888", highlight="#ffffff", shadow="#bbbbbb", offset=1
    )

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
    