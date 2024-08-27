from sqlite3 import Error
from flask import jsonify
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
    try:
        with get_db_connection() as conn:
            # 获取所有消息
            messages = conn.execute(
                'SELECT id, message_id, message_type FROM messages').fetchall()
            message_list = []

            for message in messages:
                message_id = message['id']
                # 获取对应的消息体
                message_bodies = conn.execute(
                    'SELECT key, data_type, min, max, value, value_type FROM message_bodies WHERE message_id = ?', (message_id,)).fetchall()
                bodies = [dict(body) for body in message_bodies]

                # 组合消息和消息体
                message_data = {
                    'id': message['id'],
                    'message_id': message['message_id'],
                    'message_type': message['message_type'],
                    'bodies': bodies
                }
                message_list.append(message_data)

            return jsonify(message_list)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/message', methods=['POST'])
def create_message():
    new_message = request.get_json()
    message_id = new_message['message_id']
    message_type = new_message['message_type']
    message_bodies = new_message['message_bodies']  # 包含多个消息体的列表

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO messages (message_id, message_type)
        VALUES (?, ?)
    ''', (message_id, message_type))

    message_db_id = cursor.lastrowid

    for body in message_bodies:
        key = body['key']
        data_type = body['data_type']
        min_val = body.get('min')
        max_val = body.get('max')
        value = body.get('value')
        value_type = body.get('value_type')

        cursor.execute('''
            INSERT INTO message_bodies (message_id, key, data_type, min, max, value,value_type)
            VALUES (?, ?, ?, ?, ?, ?,?)
        ''', (message_db_id, key, data_type, min_val, max_val, value, value_type))

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
    try:
        conn.execute('''
            INSERT INTO data_types (data_type)
            VALUES (?)
        ''', (new_data_type,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Data type already exists'}), 400
    conn.close()
    return '', 201


if __name__ == '__main__':
    init_db()  # 在应用启动时初始化数据库
    app.run(debug=True)
