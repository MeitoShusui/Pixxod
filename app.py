from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = "pixxod_ultimate_2026_stable"

# --- YAPILANDIRMA ---
DATABASE = 'database.db'
UPLOAD_FOLDER = os.path.join('static', 'assets', 'img', 'products')
VIDEO_UPLOAD_FOLDER = os.path.join('static', 'assets', 'img', 'videos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

# Klasörlerin varlığını kontrol et
for folder in [UPLOAD_FOLDER, VIDEO_UPLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Medya Tablosu
    conn.execute('''CREATE TABLE IF NOT EXISTS media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, category TEXT, url TEXT, poster TEXT, media_type TEXT, sort_order INTEGER DEFAULT 0)''')
    
    # Kategoriler Tablosu (Kategori ekleme sorunu için bu kısım kritiktir)
    conn.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    
    # Tablo boşsa varsayılanları ekle
    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        conn.executemany("INSERT INTO categories (name) VALUES (?)", [('product',), ('model',), ('food',)])
    
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- WEB SİTESİ ROTALARI ---

@app.route('/')
def index(): return render_template('index.html')

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/portfolio')
def portfolio():
    conn = get_db_connection()
    photos = conn.execute("SELECT * FROM media WHERE media_type='photo' ORDER BY sort_order ASC, id DESC").fetchall()
    categories = conn.execute("SELECT * FROM categories").fetchall() #
    conn.close()
    return render_template('portfolio.html', photos=photos, categories=categories)

@app.route('/video-galery')
def video_gallery():
    conn = get_db_connection()
    videos = conn.execute("SELECT * FROM media WHERE media_type='video' ORDER BY sort_order ASC, id DESC").fetchall()
    conn.close()
    return render_template('video-galery.html', videos=videos)

@app.route('/contact')
def contact(): return render_template('contact.html')

# --- ADMİN PANELİ VE KATEGORİ YÖNETİMİ ---

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    conn = get_db_connection()
    active_tab = request.args.get('tab', 'photo') #

    if request.method == 'POST':
        titles, cats, types, orders = request.form.getlist('title[]'), request.form.getlist('category[]'), request.form.getlist('media_type[]'), request.form.getlist('sort_order[]')
        files, posters = request.files.getlist('file[]'), request.files.getlist('poster[]') #
        
        for i in range(len(files)):
            file = files[i]
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                m_type = types[i]
                target = VIDEO_UPLOAD_FOLDER if m_type == 'video' else UPLOAD_FOLDER
                file.save(os.path.join(target, filename))
                db_p = f"assets/img/{'videos' if m_type == 'video' else 'products'}/{filename}"
                
                post_p = None
                if m_type == 'video' and i < len(posters) and posters[i].filename != '':
                    p_name = "poster_" + secure_filename(posters[i].filename)
                    posters[i].save(os.path.join(VIDEO_UPLOAD_FOLDER, p_name))
                    post_p = f"assets/img/videos/{p_name}"
                
                conn.execute("INSERT INTO media (title, category, url, poster, media_type, sort_order) VALUES (?,?,?,?,?,?)",
                             (titles[i], cats[i], db_p, post_p, m_type, int(orders[i]) if orders[i] else 1))
        conn.commit()
        return redirect(url_for('admin', tab=active_tab))

    per_page = 10
    p_page, v_page = request.args.get('p_page', 1, type=int), request.args.get('v_page', 1, type=int) #
    
    p_photos = conn.execute("SELECT * FROM media WHERE media_type='photo' ORDER BY sort_order ASC LIMIT ? OFFSET ?", (per_page, (p_page-1)*per_page)).fetchall()
    v_videos = conn.execute("SELECT * FROM media WHERE media_type='video' ORDER BY sort_order ASC LIMIT ? OFFSET ?", (per_page, (v_page-1)*per_page)).fetchall()
    cats = conn.execute("SELECT * FROM categories").fetchall() #
    
    p_total = conn.execute("SELECT COUNT(*) FROM media WHERE media_type='photo'").fetchone()[0]
    v_total = conn.execute("SELECT COUNT(*) FROM media WHERE media_type='video'").fetchone()[0]
    
    conn.close()
    return render_template('admin.html', photos=p_photos, p_page=p_page, p_total_pages=(p_total+per_page-1)//per_page, p_total_count=p_total,
                           videos=v_videos, v_page=v_page, v_total_pages=(v_total+per_page-1)//per_page, v_total_count=v_total,
                           categories=cats, active_tab=active_tab)

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('category_name').lower().strip() #
    if name:
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
        except: pass
        conn.close()
    return redirect(url_for('admin', tab='category')) # İşlem sonrası kategori sekmesine döner

@app.route('/delete_category/<int:cat_id>')
@login_required
def delete_category(cat_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit(); conn.close()
    return redirect(url_for('admin', tab='category'))

@app.route('/update_all', methods=['POST'])
@login_required
def update_all():
    ids, titles, cats, orders = request.form.getlist('item_id'), request.form.getlist('item_title'), request.form.getlist('item_category'), request.form.getlist('item_sort_order')
    conn = get_db_connection()
    for i in range(len(ids)):
        conn.execute("UPDATE media SET title = ?, category = ?, sort_order = ? WHERE id = ?", (titles[i], cats[i], int(orders[i]), ids[i]))
    conn.commit(); conn.close()
    return redirect(request.referrer)

@app.route('/delete_selected', methods=['POST'])
@login_required
def delete_selected():
    ids = request.form.getlist('selected_items') #
    if ids:
        conn = get_db_connection()
        placeholders = ','.join(['?']*len(ids))
        items = conn.execute(f"SELECT url, poster FROM media WHERE id IN ({placeholders})", ids).fetchall()
        for it in items:
            for path in [it['url'], it['poster']]:
                if path and os.path.exists(os.path.join('static', path)): os.remove(os.path.join('static', path))
        conn.execute(f"DELETE FROM media WHERE id IN ({placeholders})", ids)
        conn.commit(); conn.close()
    return redirect(request.referrer)

@app.route('/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM media WHERE id = ?", (item_id,)).fetchone()
    if item:
        for path in [item['url'], item['poster']]:
            if path and os.path.exists(os.path.join('static', path)): os.remove(os.path.join('static', path))
        conn.execute("DELETE FROM media WHERE id = ?", (item_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('username') == ADMIN_USERNAME and request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True; return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)