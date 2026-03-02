# -*- coding: utf-8 -*-
"""
汕头市澄海区溪南东社造纸厂开放学习平台
技术支持：南京市夜鹭云人工智能科技有限公司
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re
import os
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

DATABASE = 'learning_platform.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 数据库初始化
def init_db():
    """初始化数据库，创建表和默认管理员账号"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 创建分类表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')

    # 创建视频表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            cover_url TEXT,
            bilibili_url TEXT NOT NULL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE
        )
    ''')

    # 创建管理员表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# 获取数据库连接
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# B站链接转换函数
def convert_bilibili_url(url):
    """将B站链接转换为嵌入式播放器链接"""
    # 处理 BV 号
    bv_match = re.search(r'(BV\w+)', url)
    if bv_match:
        bvid = bv_match.group(1)
        return f'//player.bilibili.com/player.html?bvid={bvid}&page=1&high_quality=1'

    # 处理 av 号
    av_match = re.search(r'av(\d+)', url)
    if av_match:
        aid = av_match.group(1)
        return f'//player.bilibili.com/player.html?aid={aid}&page=1&high_quality=1'

    # 如果已经是嵌入式链接，直接返回
    if 'player.bilibili.com' in url:
        return url

    return url

# ========== 前台路由 ==========

@app.route('/')
def index():
    """首页 - 显示所有分类"""
    conn = get_db()
    categories = conn.execute('SELECT * FROM category ORDER BY name').fetchall()
    conn.close()
    return render_template('index.html', categories=categories)

@app.route('/category/<int:category_id>')
def category(category_id):
    """分类页面 - 显示该分类下的所有视频"""
    conn = get_db()
    category = conn.execute('SELECT * FROM category WHERE id = ?', (category_id,)).fetchone()
    if not category:
        conn.close()
        return "分类不存在", 404

    videos = conn.execute('SELECT * FROM video WHERE category_id = ?', (category_id,)).fetchall()
    conn.close()
    return render_template('category.html', category=category, videos=videos)

@app.route('/play/<int:video_id>')
def play(video_id):
    """视频播放页面"""
    conn = get_db()
    video = conn.execute('SELECT * FROM video WHERE id = ?', (video_id,)).fetchone()
    conn.close()

    if not video:
        return "视频不存在", 404

    # 转换B站链接
    embed_url = convert_bilibili_url(video['bilibili_url'])

    return render_template('play.html', video=video, embed_url=embed_url)

# ========== 后台管理路由 ==========

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        admin = conn.execute('SELECT * FROM admin WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
        conn.close()

        if admin:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('登录成功！', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('用户名或密码错误！', 'danger')

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """管理员登出"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """管理仪表盘"""
    conn = get_db()
    categories = conn.execute('SELECT * FROM category ORDER BY name').fetchall()
    videos = conn.execute('''
        SELECT v.*, c.name as category_name
        FROM video v
        LEFT JOIN category c ON v.category_id = c.id
        ORDER BY v.id DESC
    ''').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', categories=categories, videos=videos)

# ========== 分类管理 ==========

@app.route('/admin/category/add', methods=['POST'])
@login_required
def add_category():
    """添加分类"""
    name = request.form.get('name')
    description = request.form.get('description')
    if name:
        conn = get_db()
        try:
            conn.execute('INSERT INTO category (name, description) VALUES (?, ?)', (name, description))
            conn.commit()
            flash(f'分类 "{name}" 添加成功！', 'success')
        except sqlite3.IntegrityError:
            flash('分类名称已存在！', 'danger')
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/category/delete/<int:category_id>')
@login_required
def delete_category(category_id):
    """删除分类"""
    conn = get_db()
    # 检查该分类下是否有视频
    video_count = conn.execute('SELECT COUNT(*) as count FROM video WHERE category_id = ?',
                              (category_id,)).fetchone()['count']

    if video_count > 0:
        flash(f'该分类下还有 {video_count} 个视频，请先删除视频或移动到其他分类！', 'danger')
    else:
        conn.execute('DELETE FROM category WHERE id = ?', (category_id,))
        conn.commit()
        flash('分类删除成功！', 'success')

    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/category/edit/<int:category_id>', methods=['POST'])
@login_required
def edit_category(category_id):
    """编辑分类"""
    name = request.form.get('name')
    description = request.form.get('description')
    if name:
        conn = get_db()
        try:
            conn.execute('UPDATE category SET name = ?, description = ? WHERE id = ?',
                        (name, description, category_id))
            conn.commit()
            flash('分类更新成功！', 'success')
        except sqlite3.IntegrityError:
            flash('分类名称已存在！', 'danger')
        conn.close()
    return redirect(url_for('admin_dashboard'))

# ========== 视频管理 ==========

@app.route('/admin/video/add', methods=['POST'])
@login_required
def add_video():
    """添加视频"""
    title = request.form.get('title')
    description = request.form.get('description')
    cover_url = request.form.get('cover_url')
    bilibili_url = request.form.get('bilibili_url')
    category_id = request.form.get('category_id')

    # 处理文件上传
    if 'cover_file' in request.files:
        file = request.files['cover_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳避免文件名冲突
            import time
            filename = f"{int(time.time())}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            cover_url = f"/static/uploads/{filename}"

    if title and bilibili_url and category_id:
        conn = get_db()
        conn.execute('''
            INSERT INTO video (title, description, cover_url, bilibili_url, category_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, cover_url, bilibili_url, category_id))
        conn.commit()
        conn.close()
        flash(f'视频 "{title}" 添加成功！', 'success')
    else:
        flash('请填写所有必填项！', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/video/edit/<int:video_id>', methods=['POST'])
@login_required
def edit_video(video_id):
    """编辑视频"""
    title = request.form.get('title')
    description = request.form.get('description')
    cover_url = request.form.get('cover_url')
    bilibili_url = request.form.get('bilibili_url')
    category_id = request.form.get('category_id')

    # 处理文件上传
    if 'cover_file' in request.files:
        file = request.files['cover_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳避免文件名冲突
            import time
            filename = f"{int(time.time())}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            cover_url = f"/static/uploads/{filename}"

    if title and bilibili_url and category_id:
        conn = get_db()
        conn.execute('''
            UPDATE video
            SET title = ?, description = ?, cover_url = ?, bilibili_url = ?, category_id = ?
            WHERE id = ?
        ''', (title, description, cover_url, bilibili_url, category_id, video_id))
        conn.commit()
        conn.close()
        flash('视频更新成功！', 'success')
    else:
        flash('请填写所有必填项！', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/video/delete/<int:video_id>')
@login_required
def delete_video(video_id):
    """删除视频"""
    conn = get_db()
    conn.execute('DELETE FROM video WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()
    flash('视频删除成功！', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
