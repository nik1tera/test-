from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    default_data = {
        "title": "Школьный музей Школы №367",
        "description": "Школьный музей школы №367 — это не просто место...",
        "content": [
            {
                "type": "text",
                "id": "text_1",
                "content": "Пример текстового блока",
                "photos": [
                    {
                        "image": "static/uploads/example.jpg",
                        "caption": "Пример фотографии"
                    }
                ]
            }
        ]
    }
    
    try:
        if os.path.exists('museum_data.json'):
            with open('museum_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading data: {e}")
    
    return default_data

def save_data(data):
    try:
        with open('museum_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")
        flash('Ошибка сохранения данных', 'danger')

@app.route("/")
def home():
    data = load_data()
    return render_template("article.html", article=data)

@app.route("/admin", methods=['GET', 'POST'])
def admin():
    data = load_data()
    
    if request.method == 'POST':
        try:
            # Обработка загрузки файлов
            file_paths = {}
            for key in request.files:
                file = request.files[key]
                if file and file.filename and allowed_file(file.filename):
                    filename = f"{datetime.now().timestamp()}_{secure_filename(file.filename)}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    file_paths[key] = f"static/uploads/{filename}"
                    flash(f'Файл {filename} успешно загружен', 'success')

            # Обработка добавления фото
            if 'add_photo' in request.form:
                content_index = int(request.form['add_photo'])
                if 0 <= content_index < len(data['content']):
                    data['content'][content_index]['photos'].append({
                        "image": "",
                        "caption": ""
                    })
                    save_data(data)
                return redirect(url_for('admin'))

            # Удаление контента
            if 'delete_content' in request.form:
                index = int(request.form['delete_content'])
                if 0 <= index < len(data['content']):
                    data['content'].pop(index)
                    save_data(data)
                return redirect(url_for('admin'))
            
            # Добавление нового контента
            if 'add_content' in request.form:
                content_type = request.form.get('new_content_type', 'text')
                new_id = f"{content_type}_{len(data['content']) + 1}"
                
                new_item = {
                    "type": content_type,
                    "id": new_id,
                    "photos": []
                }
                
                if content_type == 'text':
                    new_item["content"] = "Новый текстовый блок"
                elif content_type == 'modal':
                    new_item.update({
                        "title": "Новое модальное окно",
                        "content": "<p>Содержимое модального окна</p>",
                        "button_text": "Кнопка",
                        "button_class": "btn-modal"
                    })
                
                data['content'].append(new_item)
                save_data(data)
                return redirect(url_for('admin'))
            
            # Обновление основных данных
            data['title'] = request.form.get('title', data['title'])
            data['description'] = request.form.get('description', data['description'])
            
            # Обработка контента
            new_content = []
            i = 0
            while True:
                content_type = request.form.get(f'content_{i}_type')
                if not content_type:
                    break
                
                # Обработка фотографий
                photos = []
                j = 1
                while True:
                    image = request.form.get(f'content_{i}_photos_{j}_image', '')
                    caption = request.form.get(f'content_{i}_photos_{j}_caption', '')
                    
                    # Проверяем загружен ли файл для этого поля
                    file_key = f'content_{i}_photo_{j}'
                    if file_key in file_paths:
                        image = file_paths[file_key]
                    
                    if not image and not caption:
                        break
                        
                    photos.append({
                        "image": image,
                        "caption": caption
                    })
                    j += 1
                
                # Создаем элемент контента
                content_item = {
                    "type": content_type,
                    "id": request.form.get(f'content_{i}_id', f"{content_type}_{i}"),
                    "photos": photos
                }
                
                if content_type == 'text':
                    content_item["content"] = request.form.get(f'content_{i}_text', '')
                elif content_type == 'modal':
                    content_item.update({
                        "title": request.form.get(f'content_{i}_modal_title', ''),
                        "content": request.form.get(f'content_{i}_modal_content', ''),
                        "button_text": request.form.get(f'content_{i}_button_text', ''),
                        "button_class": request.form.get(f'content_{i}_button_class', 'btn-modal')
                    })
                
                new_content.append(content_item)
                i += 1
            
            data['content'] = new_content
            save_data(data)
            flash('Все изменения успешно сохранены', 'success')
        
        except Exception as e:
            print(f"Error processing form: {e}")
            flash('Произошла ошибка при обработке формы', 'danger')
        
        return redirect(url_for('admin'))
    
    return render_template("admin.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)