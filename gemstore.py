from helpers import to_cents

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