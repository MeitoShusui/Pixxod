import sqlite3
import os

# --- YAPILANDIRMA ---
DATABASE = 'database.db'
# Resimlerin bulunduğu klasör yolu (Products olarak güncellendi)
UPLOAD_FOLDER = os.path.join('static', 'assets', 'img', 'products')
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.webp'}

def reset_and_import():
    # Klasör var mı kontrol et
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"HATA: '{UPLOAD_FOLDER}' yolu bulunamadı! Lütfen klasör ismini kontrol et.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("--- Veritabanı Temizlik ve Ürün Aktarımı Başladı ---")

    # 1. Tabloyu Sıfırla (Eski hatalı verilerden kurtulmak için)
    cursor.execute("DROP TABLE IF EXISTS media")
    cursor.execute('''
        CREATE TABLE media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            url TEXT,
            poster TEXT,
            media_type TEXT,
            sort_order INTEGER DEFAULT 0
        )
    ''')
    print("Veritabanı tablosu sıfırlandı.")

    # 2. Klasörü Tara
    files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS]
    files.sort() # Alfabetik sıralama (A-Z)

    if not files:
        print(f"UYARI: '{UPLOAD_FOLDER}' içinde uygun formatta dosya bulunamadı!")
        conn.close()
        return

    # 3. Benzersiz Sıra Numarası ile Ekleme
    for index, filename in enumerate(files):
        # Veritabanına kaydedilecek yol
        db_path = f"assets/img/products/{filename}"
        
        # Tür belirleme
        m_type = 'video' if filename.lower().endswith(('.mp4', '.mov')) else 'photo'
        
        # Benzersiz sıra numarası (1, 2, 3...)
        current_order = index + 1
        
        cursor.execute("""
            INSERT INTO media (title, category, url, media_type, sort_order) 
            VALUES (?, ?, ?, ?, ?)
        """, (filename.split('.')[0], 'product', db_path, m_type, current_order))
        
        print(f"[{current_order}] Eklendi: {filename}")

    conn.commit()
    conn.close()
    print(f"\nİŞLEM BAŞARILI! {len(files)} ürün benzersiz sıralama ile aktarıldı.")

if __name__ == "__main__":
    reset_and_import()