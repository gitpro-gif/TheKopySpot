import qrcode
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "https://thekopyspot.streamlit.app/")
QR_DIR = "qr_codes"

def generate_qr_for_tables(num_tables=10):
    os.makedirs(QR_DIR, exist_ok=True)
    for table in range(1, num_tables + 1):
        url = f"{BASE_URL}/?table={table}"
        img = qrcode.make(url)
        path = os.path.join(QR_DIR, f"table_{table}.png")
        img.save(path)
        print(f"✅ QR generated for Table {table}: {url}")

if __name__ == "__main__":
    generate_qr_for_tables(10)
