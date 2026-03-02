import sqlite3
import os

# --- YAPILANDIRMA ---
DATABASE = 'database.db'
# Videoların bulunduğu yeni klasör yolu
VIDEO_DIR = os.path.join('static', 'assets', 'img', 'videos')
# Desteklenen formatlar
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm', '.avi', '.mkv'}

def video_tara_ve_kaydet():
    if not os.path.exists(VIDEO_DIR):
        print(f"Hata: {VIDEO_DIR} klasörü bulunamadı! Lütfen klasörü oluşturun.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(sort_order) FROM media")
    max_order = cursor.fetchone()[0]
    sort_order = (max_order + 1) if max_order is not None else 1

    count = 0
    for dosya_adi in os.listdir(VIDEO_DIR):
        uzanti = os.path.splitext(dosya_adi)[1].lower()
        
        if uzanti in VIDEO_EXTENSIONS:
            # ÖNEMLİ: Veritabanına kaydedilecek yol
            db_yolu = f"assets/img/videos/{dosya_adi}"
            
            cursor.execute("SELECT id FROM media WHERE url = ?", (db_yolu,))
            if not cursor.fetchone():
                baslik = os.path.splitext(dosya_adi)[0].replace('_', ' ').replace('-', ' ').title()
                
                cursor.execute("""
                    INSERT INTO media (title, category, url, media_type, sort_order) 
                    VALUES (?, ?, ?, ?, ?)
                """, (baslik, 'product', db_yolu, 'video', sort_order))
                
                print(f"Eklendi: {dosya_adi}")
                sort_order += 1
                count += 1

    conn.commit()
    conn.close()
    print(f"\nİşlem tamamlandı: {count} yeni video eklendi.")

if __name__ == '__main__':
    video_tara_ve_kaydet()