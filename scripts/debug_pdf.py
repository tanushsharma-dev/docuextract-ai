import sys, os, glob
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.extraction.preprocessing import preprocess_document
from app.extraction.vlm import extract_with_vlm

pdfs = glob.glob("storage/uploads/*.pdf")
if not pdfs:
    print("❌ Koi PDF nahi mili - pehle UI se ek PDF upload karo")
    sys.exit()

pdf = max(pdfs, key=os.path.getmtime)
print("📄 Testing:", pdf, "|", os.path.getsize(pdf), "bytes")

print("\n--- STEP 1: Preprocessing ---")
paths = preprocess_document(pdf, "storage/processed/debug")
print("Pages generated:", paths)
for p in paths:
    print("  →", p, "|", os.path.getsize(p), "bytes")

print("\n--- STEP 2: Gemini Direct PDF ---")
result = extract_with_vlm(pdf, "invoice")
print("RESULT:")
print(result)