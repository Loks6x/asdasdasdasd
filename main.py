import sqlite3
import os
import logging
import html
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = "8982256451:AAFge6oA28B_khpKBAhYrQC6NbzQRFhusMk"
CHAT_ID = -1005307316313  

bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

DB_PATH = "orders.db"

# --- ПОЛНОЕ МЕНЮ (40 ПОЗИЦИЙ С КАЛЬКУЛЯТОРАМИ) ---
INITIAL_MENU = [
    {"tab": "drinks", "category": "cocktail", "title": "Апероль Спритз", "method": "Заливаем все в бокал для красного вина с кусковым льдом и перемешиваем, украшаем слайсом апельсина", "tags": '["220 мл", "Лед"]', "glass": "Бокал для красного вина", "ingredients": '["Ликер Aperol - 60 мл", "Игристое Абрау Дюрсо - 100 мл", "Содовая - 30 мл", "Апельсин - 30 гр"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Беллини", "method": "Заливаем все в блендер, немного взбиваем, и переливаем в шале. Украшаем цветком", "tags": '["200 мл"]', "glass": "Креманка", "ingredients": '["Пф Беллини - 80 мл", "Игристое вино Шато Двуморье брют - 120 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Негрони", "method": "Заливаем все ингридиенты в смес, стируем и переливаем в бокал олд фешн со льдом, украшаем цедрой апельсина.", "tags": '["90 мл", "Лед"]', "glass": "Рокс", "ingredients": '["Джин Bikens - 30 мл", "Cinzano 1757 rosso - 30 мл", "Campari - 30 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Бэзил Смеш", "method": "Заливаем все в шейкер с кусковым льдом, подаем в олд фэшн со льдом и украшаем листом базилика.", "tags": '["80 мл", "Лед"]', "glass": "Рокс", "ingredients": '["Джин - 40 мл", "Сахарный сироп - 20 мл", "Пф лимонный фреш - 20 мл", "Базилик свежий - 8 гр"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Татарский Олд Фэшн", "method": "Заливаем все в смес, стируем и переливаем в бокал олд фэшн. Украшение: Окуриваем бокал окуривателем и щепой.", "tags": '["70 мл"]', "glass": "Рокс", "ingredients": '["Пф Бурбон/Курага - 70 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Лимончелло Спритз", "method": "Заливаем все в бокал для красного вина с кусковым льдом и перемешиваем, украшаем листьями мяты и долькой лимона", "tags": '["180 мл", "Лед"]', "glass": "Бокал для красного вина", "ingredients": '["Пф Лимончелло - 60 мл", "Игристое Абрау Дюрсо - 90 мл", "Газированная вода - 30 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Мартини-Эспрессо", "method": "Заливаем все в шейкер с кусковым льдом, подаем в креманку и украшаем зерновым кофе.", "tags": '["115 мл", "Лед"]', "glass": "Креманка", "ingredients": '["Водка Белуга Нобл - 40 мл", "Эспрессо - 40 мл", "Мари Бризар Кофе - 25 мл", "Сахарный сироп - 10 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Май-Тай", "method": "Заливаем все в шейкер с кусковым льдом, подаем в олд фэшн с колотым льдом и украшаем сушеным апельсином и пылью из каркаде.", "tags": '["140 мл", "Лед", "Краш"]', "glass": "Рокс", "ingredients": '["Ром Барсело Бланко - 30 мл", "Ром Такамака - 30 мл", "Трипл Сек - 30 мл", "Амаретто - 10 мл", "Сахарный сироп - 10 мл", "Фреш лайма - 30 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Маргарита", "method": "Заливаем все в шейкер с кусковым льдом, подаем в креманку с каемкой из соли и долькой лайма", "tags": '["90 мл", "Лед"]', "glass": "Креманка", "ingredients": '["Текила Агавита - 40 мл", "Трипл Сек - 20 мл", "Сахарный Сироп - 10 мл", "Фреш лайма - 20 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Сарти Шпритц", "method": "Заливаем все в бокал для красного вина с кусковым льдом и перемешиваем, украшаем слайсом лайма", "tags": '["180 мл", "Лед"]', "glass": "Бокал для красного вина", "ingredients": '["Игристое Абрау Дюрсо - 90 мл", "Ликер Сарти - 60 мл", "Газированная вода - 30 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Венецианский Шпритц", "method": "Заливаем все в бокал для красного вина с кусковым льдом и перемешиваем, украшаем слайсом грейпфрута", "tags": '["190 мл", "Лед"]', "glass": "Бокал для красного вина", "ingredients": '["Кампари - 60 мл", "Игристое Абрау Дюрсо - 70 мл", "Сок грейпфрута - 30 мл", "Газированная вода - 30 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "cocktail", "title": "Порн Стар Мартини", "method": "Заливаем все в шейкер с кусковым льдом (шейк+драй шейк) или мини блендер с фрапе, переливаем в шале и урашаем и отдельно подаем шот игристого 50 мл", "tags": '["160 мл", "Лед"]', "glass": "Креманка", "ingredients": '["Пф Маракуйя - 60 мл", "Водка Lab ваниль и бобы тонка - 50 мл", "Игристое Шато Двуморье брют - 50 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "lemonade", "title": "Малина с персиком", "method": "Заливаем все ингридиенты в хайбол с кусковым льдом, перемешиваем и украшаем цветком", "tags": '["160 мл", "Лед"]', "glass": "Хайбол", "ingredients": '["Пф Малина/Персик - 70 мл", "Содовая - 90 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "lemonade", "title": "Манго и маракуйя", "method": "Заливаем все ингридиенты в хайбол с кусковым льдом, перемешиваем и украшаем цветком", "tags": '["160 мл", "Лед"]', "glass": "Хайбол", "ingredients": '["Пф Тропики - 70 мл", "Содовая - 90 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "smoothie", "title": "Зеленый смузи", "method": "Закидываем все в блендер и переливаем в хайбол", "tags": '["350 мл"]', "glass": "Хайбол", "ingredients": '["Огурец - 100 гр", "Яблоко - 100 гр", "Лимон - 40 гр", "Базилик - 5 гр", "Мята - 3 гр", "Сахарный сироп - 10 мл", "Вода - 50 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "smoothie", "title": "Цитрус-Имбирь", "method": "Закидываем все в блендер и переливаем в хайбол", "tags": '["350 мл", "Лед"]', "glass": "Хайбол", "ingredients": '["Апельсин - 120 гр", "Грейпфрут - 120 гр", "Лимон - 40 гр", "Имбирь - 15 гр", "Мед - 15 гр", "Лед - 50 гр"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "tea_coffee", "title": "Чай Смородина с базиликом", "method": "Закидываем все в чайник и кипятим", "tags": '["700 мл"]', "glass": "Чайник", "ingredients": '["Пюре смородины - 120 гр", "Базилик свежий - 10 гр", "Пф сахарный сироп - 60 мл", "Эрл грей - 5 гр"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "tea_coffee", "title": "Капучино", "method": "Готовим на 1/2 кофе", "tags": '["250 мл"]', "glass": "Кружка", "ingredients": '["Кофе - 18 гр", "Молоко - 200 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {"tab": "drinks", "category": "nonalk", "title": "Маргарита 0.0", "method": "Заливаем все в шейкер с кусковым льдом, подаем в креманку с каемкой из соли и долькой лайма", "tags": '["90 мл", "Лед"]', "glass": "Креманка", "ingredients": '["Дринксом текила - 40 мл", "Дринксом апельсин - 20 мл", "Сахарный сироп - 10 мл", "Фреш лайма - 20 мл"]', "baseYield": 0, "unit": "", "calcIngredients": "[]"},
    {
        "tab": "pf", "category": "pf", "title": "Пф Микс кислот", "method": "Все смешиваем в мернике и переливаем в бутылку", 
        "tags": '["Заготовка"]', "glass": "", "ingredients": "[]", "baseYield": 500, "unit": "мл", 
        "calcIngredients": '[{"name": "Лимонная кислота", "amount": 16, "unit": "гр"}, {"name": "Винная кислота", "amount": 8, "unit": "гр"}, {"name": "Яблочная кислота", "amount": 12, "unit": "гр"}, {"name": "Вода", "amount": 1000, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Сахарный сироп", "method": "Все засыпаем в сотейник, варим до растворения сахара, переливаем в бутылку", 
        "tags": '["Заготовка"]', "glass": "", "ingredients": "[]", "baseYield": 1000, "unit": "мл", 
        "calcIngredients": '[{"name": "Сахар", "amount": 900, "unit": "гр"}, {"name": "Вода", "amount": 700, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Алоэ", "method": "Алоэ воду фильтруем через сито и переливаем в мерный стакан, добавляем все ингридиенты и смешиваем", 
        "tags": '["Заготовка"]', "glass": "", "ingredients": "[]", "baseYield": 650, "unit": "мл", 
        "calcIngredients": '[{"name": "Вода", "amount": 250, "unit": "мл"}, {"name": "Напиток Алоэ", "amount": 250, "unit": "мл"}, {"name": "Пф сахарный сироп", "amount": 100, "unit": "мл"}, {"name": "Пф Микс кислот", "amount": 50, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Клубника/цитрус", "method": "Все ингридиенты засыпаем в вакуумный пакет и сювидим на 55 градусах 4 часа", 
        "tags": '["Заготовка", "Су-вид"]', "glass": "", "ingredients": "[]", "baseYield": 800, "unit": "мл", 
        "calcIngredients": '[{"name": "Клубника с/м", "amount": 250, "unit": "гр"}, {"name": "Luxardo Aperitivo", "amount": 400, "unit": "мл"}, {"name": "Сахар", "amount": 150, "unit": "гр"}, {"name": "Лимонный фреш", "amount": 150, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Мэри", "method": "Засыпаем все в блендер, перебиваем и заливаем в бутылку", 
        "tags": '["Заготовка"]', "glass": "", "ingredients": "[]", "baseYield": 500, "unit": "мл", 
        "calcIngredients": '[{"name": "Томаты в с/с", "amount": 300, "unit": "гр"}, {"name": "Сок томатный", "amount": 150, "unit": "мл"}, {"name": "Апельсины", "amount": 250, "unit": "гр"}, {"name": "Ворчестер", "amount": 35, "unit": "гр"}, {"name": "Табаско", "amount": 5, "unit": "гр"}, {"name": "Пф микс кислот", "amount": 10, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Бурбон/Курага", "method": "Засыпаем все в вакуумный пакет и сювидим 4 часа на 55 градусах", 
        "tags": '["Заготовка", "Су-вид"]', "glass": "", "ingredients": "[]", "baseYield": 450, "unit": "мл", 
        "calcIngredients": '[{"name": "Бурбон Jim Beam", "amount": 500, "unit": "мл"}, {"name": "Курага", "amount": 100, "unit": "гр"}, {"name": "Пф кордиал мед", "amount": 100, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Беллини", "method": "Заливаем все в сотейник и варим, затем цедим в бутылку", 
        "tags": '["Заготовка"]', "glass": "", "ingredients": "[]", "baseYield": 1200, "unit": "мл", 
        "calcIngredients": '[{"name": "Пюре персик", "amount": 500, "unit": "гр"}, {"name": "Сок персиковый", "amount": 250, "unit": "мл"}, {"name": "Сахар", "amount": 250, "unit": "гр"}, {"name": "Вода", "amount": 250, "unit": "мл"}, {"name": "Пф лимонный фреш", "amount": 300, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Лимончелло", "method": "Снимаем цедру без альбедо, в вакуум с водкой на 5 часов 50 град. Добавляем лимон фреш и сироп.", 
        "tags": '["Заготовка", "Су-вид"]', "glass": "", "ingredients": "[]", "baseYield": 800, "unit": "мл", 
        "calcIngredients": '[{"name": "Водка Organic", "amount": 500, "unit": "мл"}, {"name": "Лимоны", "amount": 400, "unit": "гр"}, {"name": "Пф сахарный сироп", "amount": 150, "unit": "мл"}]'
    },
    {
        "tab": "pf", "category": "pf", "title": "Пф Тропики", "method": "Смешиваем", 
        "tags": '["Заготовка"]', "glass": "", "ingredients": "[]", "baseYield": 700, "unit": "мл", 
        "calcIngredients": '[{"name": "Пюре манго", "amount": 300, "unit": "гр"}, {"name": "Пюре маракуйя", "amount": 150, "unit": "гр"}, {"name": "Пф сахарный сироп", "amount": 100, "unit": "мл"}, {"name": "Микс кислот", "amount": 100, "unit": "мл"}]'
    }
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_order (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity TEXT NOT NULL,
        comment TEXT,
        author_name TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tab TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        method TEXT,
        tags TEXT,
        glass TEXT,
        ingredients TEXT,
        baseYield INTEGER,
        unit TEXT,
        calcIngredients TEXT
    )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    if cursor.fetchone()[0] == 0:
        logger.info("База меню пуста. Загружаю стартовое меню...")
        for item in INITIAL_MENU:
            cursor.execute("""
                INSERT INTO menu_items (tab, category, title, method, tags, glass, ingredients, baseYield, unit, calcIngredients)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item['tab'], item['category'], item['title'], item['method'], item['tags'], item['glass'], item['ingredients'], item['baseYield'], item['unit'], item['calcIngredients']))
    
    conn.commit()
    conn.close()

init_db()

async def send_order_to_tg():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, quantity, comment, author_name FROM active_order ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    
    if not rows:
        conn.close()
        return False

    authors = set()
    items_list = []
    for r in rows:
        name, qty, comm, auth = r
        authors.add(html.escape(auth))
        c_part = f" (<i>{html.escape(comm)}</i>)" if comm else ""
        items_list.append(f"• <b>{html.escape(name)}</b> — {html.escape(qty)}{c_part}")
    
    message = "📦 <b>НОВАЯ ЗАЯВКА</b>\n\n" + "\n".join(items_list) + f"\n\n👤 <b>Кто составил:</b> {', '.join(authors)}"
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)
        cursor.execute("DELETE FROM active_order")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка ТГ: {e}")
        return False
    finally:
        conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(send_order_to_tg, 'cron', hour=8, minute=0)
    scheduler.add_job(send_order_to_tg, 'cron', hour=20, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrderItem(BaseModel):
    item_name: str
    quantity: str
    comment: str = ""
    author_name: str

class MenuItemBase(BaseModel):
    tab: str
    category: str
    title: str
    method: str = ""
    tags: str = "[]"
    glass: str = ""
    ingredients: str = "[]"
    baseYield: int = 0
    unit: str = ""
    calcIngredients: str = "[]"

# --- СЕКРЕТНАЯ КНОПКА СБРОСА БАЗЫ ДАННЫХ ---
@app.get("/api/force_reset_menu")
async def force_reset_menu():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Удаляем старую базу меню
    cursor.execute("DROP TABLE IF EXISTS menu_items")
    conn.commit()
    conn.close()
    
    # Создаем ее заново и заливаем 40 позиций
    init_db()
    
    return {"message": "УРА! База данных успешно сброшена. Все 40 позиций с калькуляторами загружены! Можешь закрывать эту страницу и возвращаться в приложение."}

# --- ОСТАЛЬНЫЕ ЭНДПОИНТЫ ---
@app.get("/api/get_orders")
async def get_orders():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, quantity, comment, author_name FROM active_order ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "item_name": r[1], "quantity": r[2], "comment": r[3], "author_name": r[4]} for r in rows]

@app.post("/api/add_order")
async def add_order(item: OrderItem):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO active_order (item_name, quantity, comment, author_name) VALUES (?, ?, ?, ?)", (item.item_name, item.quantity, item.comment, item.author_name))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/delete_order/{order_id}")
async def delete_order(order_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_order WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/send_now")
async def send_now():
    success = await send_order_to_tg()
    if not success:
        raise HTTPException(status_code=500, detail="Ошибка отправки в Telegram.")
    return {"status": "success"}

@app.get("/api/menu")
async def get_menu():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, tab, category, title, method, tags, glass, ingredients, baseYield, unit, calcIngredients FROM menu_items")
    rows = cursor.fetchall()
    conn.close()
    menu = []
    for r in rows:
        menu.append({
            "id": r[0], "tab": r[1], "category": r[2], "title": r[3], "method": r[4],
            "tags": json.loads(r[5] if r[5] else "[]"),
            "glass": r[6],
            "ingredients": json.loads(r[7] if r[7] else "[]"),
            "baseYield": r[8], "unit": r[9],
            "calcIngredients": json.loads(r[10] if r[10] else "[]")
        })
    return menu

@app.post("/api/menu")
async def add_menu_item(item: MenuItemBase):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO menu_items (tab, category, title, method, tags, glass, ingredients, baseYield, unit, calcIngredients)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (item.tab, item.category, item.title, item.method, item.tags, item.glass, item.ingredients, item.baseYield, item.unit, item.calcIngredients))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/menu/{item_id}")
async def delete_menu_item(item_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.get("/logo.png")
async def serve_logo():
    if os.path.exists("logo.png"): return FileResponse("logo.png")
    raise HTTPException(status_code=404, detail="Логотип не найден")
