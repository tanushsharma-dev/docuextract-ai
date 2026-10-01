import os
from PIL import Image, ImageDraw, ImageFont

OUT = "storage/samples"
os.makedirs(OUT, exist_ok=True)

def fonts():
    try:
        big = ImageFont.truetype("arial.ttf", 26)
        mid = ImageFont.truetype("arial.ttf", 20)
        small = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        big = mid = small = ImageFont.load_default()
    return big, mid, small

BIG, MID, SMALL = fonts()

def make_receipt():
    img = Image.new("RGB", (500, 900), "white")
    d = ImageDraw.Draw(img)
    d.text((150, 40), "CITY MART", fill="black", font=BIG)
    d.text((130, 75), "SUPERSTORE PVT LTD", fill="black", font=SMALL)
    d.text((140, 100), "MG Road, Bengaluru", fill="black", font=SMALL)
    d.text((130, 140), "Date: 12/03/2026", fill="black", font=SMALL)
    d.text((110, 165), "Receipt No: RCT-8841", fill="black", font=SMALL)
    d.line([(40, 200), (460, 200)], fill="black", width=1)
    d.text((50, 220), "Milk 1L x2", fill="black", font=SMALL)
    d.text((390, 220), "110.00", fill="black", font=SMALL)
    d.text((50, 250), "Bread", fill="black", font=SMALL)
    d.text((390, 250), "45.00", fill="black", font=SMALL)
    d.text((50, 280), "Eggs x12", fill="black", font=SMALL)
    d.text((390, 280), "90.00", fill="black", font=SMALL)
    d.line([(40, 320), (460, 320)], fill="black", width=1)
    d.text((250, 340), "Subtotal: 245.00", fill="black", font=SMALL)
    d.text((250, 370), "Tax: 12.25", fill="black", font=SMALL)
    d.text((250, 410), "TOTAL: 257.25", fill="black", font=MID)
    d.text((250, 460), "Paid by: UPI", fill="black", font=SMALL)
    d.text((150, 800), "THANK YOU! VISIT AGAIN", fill="black", font=SMALL)
    img.save(f"{OUT}/sample_receipt.png")

def make_bank_statement():
    img = Image.new("RGB", (800, 1000), "white")
    d = ImageDraw.Draw(img)
    d.text((60, 40), "NATIONAL BANK OF INDIA", fill="black", font=BIG)
    d.text((60, 80), "ACCOUNT STATEMENT", fill="black", font=MID)
    d.text((60, 130), "Account Holder: Rahul Kumar", fill="black", font=SMALL)
    d.text((60, 160), "Account Number: 50100234567890", fill="black", font=SMALL)
    d.text((60, 190), "Statement Period: 01/08/2026 - 31/08/2026", fill="black", font=SMALL)
    d.line([(50, 230), (750, 230)], fill="black", width=2)
    d.text((60, 250), "Date", fill="black", font=SMALL)
    d.text((200, 250), "Description", fill="black", font=SMALL)
    d.text((620, 250), "Amount", fill="black", font=SMALL)
    d.line([(50, 280), (750, 280)], fill="black", width=1)
    rows = [
        ("01/08/2026", "Opening Balance", "50000.00"),
        ("05/08/2026", "Salary Credit - ACME CORP", "85000.00"),
        ("10/08/2026", "UPI - Rent Payment", "-15000.00"),
        ("15/08/2026", "ATM Withdrawal", "-5000.00"),
        ("31/08/2026", "Closing Balance", "115000.00"),
    ]
    y = 300
    for date, desc, amt in rows:
        d.text((60, y), date, fill="black", font=SMALL)
        d.text((200, y), desc, fill="black", font=SMALL)
        d.text((620, y), amt, fill="black", font=SMALL)
        y += 35
    d.line([(50, y), (750, y)], fill="black", width=1)
    d.text((60, y + 30), "Opening Balance: 50000.00", fill="black", font=MID)
    d.text((60, y + 65), "Closing Balance: 115000.00", fill="black", font=MID)
    d.text((60, y + 100), "Currency: INR", fill="black", font=SMALL)
    img.save(f"{OUT}/sample_bank_statement.png")

def make_id_card():
    img = Image.new("RGB", (800, 500), "white")
    d = ImageDraw.Draw(img)
    d.text((60, 30), "GOVERNMENT OF INDIA", fill="black", font=BIG)
    d.text((60, 70), "IDENTITY CARD", fill="black", font=MID)
    d.rectangle([(560, 60), (740, 260)], outline="black", width=2)
    d.text((610, 150), "PHOTO", fill="black", font=SMALL)
    d.text((60, 140), "Name: Rahul Kumar", fill="black", font=MID)
    d.text((60, 180), "ID Number: ID-2026-4571", fill="black", font=SMALL)
    d.text((60, 210), "Date of Birth: 15/05/1998", fill="black", font=SMALL)
    d.text((60, 240), "Issue Date: 01/01/2024", fill="black", font=SMALL)
    d.text((60, 270), "Expiry Date: 01/01/2034", fill="black", font=SMALL)
    d.text((60, 310), "Address: 221B MG Road, Mumbai", fill="black", font=SMALL)
    d.rectangle([(40, 20), (760, 480)], outline="black", width=3)
    img.save(f"{OUT}/sample_id_card.png")

def make_form():
    img = Image.new("RGB", (800, 1000), "white")
    d = ImageDraw.Draw(img)
    d.text((250, 40), "REGISTRATION FORM", fill="black", font=BIG)
    d.text((60, 120), "Full Name: Priya Sharma", fill="black", font=MID)
    d.text((60, 170), "Email: priya.sharma@email.com", fill="black", font=MID)
    d.text((60, 220), "Phone: +91 98765 43210", fill="black", font=MID)
    d.text((60, 270), "Date: 20/09/2026", fill="black", font=MID)
    d.text((60, 320), "Organization: TechCorp Ltd", fill="black", font=MID)
    d.line([(50, 380), (750, 380)], fill="black", width=2)
    d.text((60, 410), "Signature:", fill="black", font=SMALL)
    img.save(f"{OUT}/sample_form.png")

def make_invoice():
    img = Image.new("RGB", (800, 1000), "white")
    d = ImageDraw.Draw(img)
    d.text((60, 50), "ACME SUPPLIES PVT LTD", fill="black", font=BIG)
    d.text((60, 90), "123 Market Street, Mumbai", fill="black", font=SMALL)
    d.text((500, 50), "TAX INVOICE", fill="black", font=BIG)
    d.text((500, 90), "Invoice No: INV-2043", fill="black", font=SMALL)
    d.text((500, 120), "Date: 15/01/2026", fill="black", font=SMALL)
    d.line([(50, 160), (750, 160)], fill="black", width=2)
    d.text((60, 180), "Bill To: Rahul Kumar", fill="black", font=SMALL)
    d.line([(50, 230), (750, 230)], fill="black", width=2)
    d.text((60, 250), "Description", fill="black", font=SMALL)
    d.text((450, 250), "Qty", fill="black", font=SMALL)
    d.text((550, 250), "Price", fill="black", font=SMALL)
    d.text((670, 250), "Amount", fill="black", font=SMALL)
    d.line([(50, 280), (750, 280)], fill="black", width=1)
    d.text((60, 300), "Laptop Stand", fill="black", font=SMALL)
    d.text((450, 300), "2", fill="black", font=SMALL)
    d.text((550, 300), "1000.00", fill="black", font=SMALL)
    d.text((670, 300), "2000.00", fill="black", font=SMALL)
    d.line([(50, 340), (750, 340)], fill="black", width=1)
    d.text((550, 370), "Subtotal: 2000.00", fill="black", font=SMALL)
    d.text((550, 400), "Tax (18%): 360.00", fill="black", font=SMALL)
    d.text((550, 440), "Total: 2360.00", fill="black", font=BIG)
    d.text((60, 900), "Currency: INR", fill="black", font=SMALL)
    img.save(f"{OUT}/sample_invoice.png")

if __name__ == "__main__":
    make_invoice()
    make_receipt()
    make_bank_statement()
    make_id_card()
    make_form()
    print("✅ 5 sample documents generated in storage/samples/")