import os
from PIL import Image, ImageDraw, ImageFont

def make_invoice(path="data/raw/sample_invoice.png"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (800, 1000), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
        small = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
        small = font

    d.text((60, 50), "ACME SUPPLIES PVT LTD", fill="black", font=font)
    d.text((60, 90), "123 Market Street, Mumbai", fill="black", font=small)
    d.text((500, 50), "TAX INVOICE", fill="black", font=font)
    d.text((500, 90), "Invoice No: INV-2043", fill="black", font=small)
    d.text((500, 120), "Date: 15/01/2026", fill="black", font=small)
    d.line([(50, 160), (750, 160)], fill="black", width=2)
    d.text((60, 180), "Bill To: Rahul Kumar", fill="black", font=small)
    d.line([(50, 230), (750, 230)], fill="black", width=2)
    d.text((60, 250), "Description", fill="black", font=small)
    d.text((450, 250), "Qty", fill="black", font=small)
    d.text((550, 250), "Price", fill="black", font=small)
    d.text((670, 250), "Amount", fill="black", font=small)
    d.line([(50, 280), (750, 280)], fill="black", width=1)
    d.text((60, 300), "Laptop Stand", fill="black", font=small)
    d.text((450, 300), "2", fill="black", font=small)
    d.text((550, 300), "1000.00", fill="black", font=small)
    d.text((670, 300), "2000.00", fill="black", font=small)
    d.line([(50, 340), (750, 340)], fill="black", width=1)
    d.text((550, 370), "Subtotal: 2000.00", fill="black", font=small)
    d.text((550, 400), "Tax (18%): 360.00", fill="black", font=small)
    d.text((550, 440), "Total: 2360.00", fill="black", font=font)
    d.text((60, 900), "Currency: INR", fill="black", font=small)

    img.save(path)
    print(f"✅ Sample invoice saved: {path}")

if __name__ == "__main__":
    make_invoice()