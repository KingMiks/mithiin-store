from helpers import to_cents
from models import Product, db

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