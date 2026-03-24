from fastapi import FastAPI
import pandas as pd
import requests
import io
from datetime import datetime

app = FastAPI()

# URL Target
URL = "https://fiskal.kemenkeu.go.id/informasi-publik/kurs-pajak"

# Variabel untuk menyimpan data di memori (sesuai permintaan: simpan sekali)
cached_data = {
    "last_updated": None,
    "data": []
}

def scrape_kurs():
    try:
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        # 1. Ambil data dengan requests
        response = requests.get(URL, headers=header, timeout=15)
        response.raise_for_status() # Akan error jika 404 atau 500
        
        # 2. Gunakan io.StringIO untuk membungkus html string agar Pandas tidak bingung
        html_data = io.StringIO(response.text)
        
        # 3. Baca tabel dengan engine lxml secara eksplisit
        tables = pd.read_html(html_data, flavor='lxml')
        
        if not tables or len(tables) == 0:
            return {"error": "Tabel tidak ditemukan di halaman tersebut."}
            
        df = tables[0]
        
        # 4. Pembersihan nama kolom (menghilangkan spasi/karakter aneh)
        df.columns = [str(col).strip() for col in df.columns]
        
        # 5. Konversi ke list dictionary
        return df.to_dict(orient="records")
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Masalah koneksi ke Kemenkeu: {str(e)}"}
    except Exception as e:
        return {"error": f"Gagal memproses data: {str(e)}"}

@app.get("/")
def home():
    return {"message": "API Kurs Pajak Kemenkeu Aktif", "endpoint": "/api/kurs"}

@app.get("/api/update")
def force_update():
    """Endpoint untuk memicu scraping (dilakukan manual/cron per 2 minggu)"""
    data = scrape_kurs()
    cached_data["data"] = data
    cached_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"message": "Data updated successfully", "timestamp": cached_data["last_updated"]}

@app.get("/api/kurs")
def get_kurs():
    """Mengambil data yang sudah tersimpan"""
    if not cached_data["data"]:
        # Jika data kosong, lakukan scraping pertama kali
        force_update()
    return cached_data