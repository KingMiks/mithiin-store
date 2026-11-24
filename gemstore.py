from helpers import to_cents
from models import Product, db
import os
import requests
from dotenv import load_dotenv

def stone_from_api(raw):
    return {
        "stone_no": raw["Stone_NO"],
        "shape": raw["Shape"],
        "carat": float(raw["Weight"]),
        "price": to_cents(raw["SaleAmt"]),
        "cut": raw["Cut"],
        "color": raw["Color"],
        "clarity": raw["Clarity"],
        "polish": raw["Polish"],
        "symmetry": raw["Symm"],
        "lab": raw["Lab"],
        "report_no": raw["Lab_Report_No"],
        "image": raw["Stone_Img_url"],
        "certificate_url": raw["Certificate_file_url"],
        "video_url": raw["Video_url"],
    }

def stone_name(carat, shape):
    return f"{carat:.2f} ct {shape.title()} Lab-Grown Diamond"

def upsert_stone(values):
    stone = Product.query.filter_by(stone_no=values["stone_no"]).first()
    if stone is None:
        stone = Product(**values, name=stone_name(carat=values["carat"], shape=values["shape"]), stock=1, status="pending")
        db.session.add(stone)
    else:
        for key, value  in values.items():
            setattr(stone, key, value)

    return stone

def hide_missing(feed_stone_nos):
    synced = Product.query.filter(Product.stone_no.isnot(None)).all()
    hidden = 0
    for product in synced:
        if product.stone_no not in feed_stone_nos and product.status != "hidden":
            product.status = "hidden"
            hidden += 1
    return hidden

def run_sync(feed):
    api_status = feed.get("ApiStatus")
    stone_list = feed.get("StoneList", [])

    if api_status != "Success" or not stone_list:
        return {"error": "bad response"}

    existing = Product.query.filter(Product.stone_no.isnot(None), Product.status != "hidden").count()
    feed_stone_nos = set()
    upserted = 0
    skipped = 0
    for stone in stone_list:
        if stone.get("Diamond_Type") != "LABGROWN" or stone.get("StockStatus") != "AVAILABLE":
            skipped +=1
            continue
        values = stone_from_api(stone)
        if values["price"] <= 0:
            skipped +=1
            continue
        upsert_stone(values)
        feed_stone_nos.add(values["stone_no"])
        upserted +=1

    if existing > 0 and len(feed_stone_nos) < existing * 0.9:
        hidden = 0
        hide_skipped = True
    else:
        hidden = hide_missing(feed_stone_nos)
        hide_skipped = False
    db.session.commit()
    return {"upserted": upserted, "skipped": skipped, "hidden": hidden, "hide_skipped": hide_skipped}

def fetch_feed():
    url = os.getenv("GEMSTORE_API_URL", "")
    token = os.getenv("GEMSTORE_API_KEY", "")
    r = requests.post(url, params={"APIToken": token}, timeout=120)
    r.raise_for_status()
    return r.json()
