import sys
import os
import json

# Project root ko path me add karo (isse 'app' module mil jayega)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.extraction.vlm import extract_with_vlm

if len(sys.argv) < 2:
    print("Usage: python scripts/test_vlm.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]
print(f"🔍 Extracting from: {image_path}")
result = extract_with_vlm(image_path, "invoice")

if "error" in result:
    print(f"❌ Error: {result['error']}")
else:
    print("✅ Extraction successful!")
    print(json.dumps(result, indent=2))