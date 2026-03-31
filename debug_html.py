# debug_html.py

import asyncio
from parser_modules.async_request import requester


async def debug():
    url = "https://www.istu.edu/schedule/?special=vikl"

    print("🔍 Загружаем страницу...")
    html = await requester.get(url)

    if html is None:
        print("❌ Запрос не удался")
        return

    print(f"✅ Получено {len(html)} символов")

    # Сохраняем HTML в файл
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("📄 HTML сохранён в debug_page.html")

    # Ищем все class в первых 5000 символах
    import re
    classes = re.findall(r'class="([^"]+)"', html[:5000])
    print(f"\n📋 Найденные классы (первые 20):")
    for cls in classes[:20]:
        print(f"  - {cls}")

    await requester.close()

if __name__ == "__main__":
    asyncio.run(debug())
