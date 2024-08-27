from flask import Flask, request, jsonify, render_template
import sqlite3
from database import init_db  # 导入 init_db 函数

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/messages', methods=['GET'])
def get_messages():
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages').fetchall()
    conn.close()
    return jsonify([dict(row) for row in messages])

@app.route('/message', methods=['POST'])
def create_message():
    new_message = request.get_json()
    message_id = new_message['message_id']
    message_type = new_message['message_type']
    key = new_message['key']
    data_type = new_message['data_type']
    min_val = new_message.get('min')
    max_val = new_message.get('max')
    value = new_message.get('value')
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO messages (message_id, message_type, key, data_type, min, max, value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (message_id, message_type, key, data_type, min_val, max_val, value))
    conn.commit()
    conn.close()
    return jsonify(new_message), 201

@app.route('/message/<int:id>', methods=['PUT'])
def update_message(id):
    updated_message = request.get_json()
    message_id = updated_message['message_id']
    message_type = updated_message['message_type']
    key = updated_message['key']
    data_type = updated_message['data_type']
    min_val = updated_message.get('min')
    max_val = updated_message.get('max')
    value = updated_message.get('value')
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE messages
        SET message_id = ?, message_type = ?, key = ?, data_type = ?, min = ?, max = ?, value = ?
        WHERE id = ?
    ''', (message_id, message_type, key, data_type, min_val, max_val, value, id))
    conn.commit()
    conn.close()
    return jsonify(updated_message)

@app.route('/message/<int:id>', methods=['DELETE'])
def delete_message(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM messages WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/data_types', methods=['GET'])
def get_data_types():
    conn = get_db_connection()
    data_types = conn.execute('SELECT data_type FROM data_types').fetchall()
    conn.close()
    return jsonify([row['data_type'] for row in data_types])

@app.route('/data_type', methods=['POST'])
def add_data_type():
    new_data_type = request.get_json()['data_type']
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO data_types (data_type)
        VALUES (?)
    ''', (new_data_type,))
    conn.commit()
    conn.close()
    return '', 201

if __name__ == '__main__':
    init_db()  # 在应用启动时初始化数据库
    app.run(debug=True)