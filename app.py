from sqlite3 import Error
from flask import jsonify
from flask import Flask, request, jsonify, render_template
import sqlite3
from database import init_db  # 导入 init_db 函数
import json
from generatMsg import buildHeader, buildFooter, build_fields, build_complicated_msg, buildFunctionDefine, insertFunctionRoutine

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
                'SELECT id, message_id, message_name, message_type,message_size,descriptor FROM messages').fetchall()
            message_list = []

            for message in messages:
                message_name = message['message_name']
                # 获取对应的消息体
                message_bodies = conn.execute(
                    'SELECT key, data_type, length, min, max, value, value_type FROM message_bodies WHERE message_name = ?', (message_name,)).fetchall()
                bodies = [dict(body) for body in message_bodies]

                # 组合消息和消息体
                message_data = {
                    'id': message['id'],
                    'message_name': message['message_name'],
                    'message_type': message['message_type'],
                    'message_id': message['message_id'],
                    'message_size': message['message_size'],
                    'bodies': bodies
                }

                if message['descriptor']:
                    message_data['descriptor'] = json.loads(
                        message['descriptor'])
                message_list.append(message_data)

            return jsonify(message_list)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/message', methods=['POST'])
def create_message():
    new_message = request.get_json()
    message_name = new_message['message_name']
    message_type = new_message['message_type']
    message_id = new_message['message_id']
    message_size = new_message['message_size']
    descriptor = new_message.get('descriptor')
    descriptor = json.dumps(descriptor)
    message_bodies = new_message['message_bodies']  # 包含多个消息体的列表

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO messages (message_id, message_name, message_type, message_size,descriptor)
        VALUES (?, ?,?,?,?)
    ''', (message_id, message_name, message_type, message_size, descriptor))

    message_db_id = cursor.lastrowid

    for body in message_bodies:
        key = body['key']
        data_type = body['data_type']
        min_val = body.get('min')
        max_val = body.get('max')
        value = body.get('value')
        value_type = body.get('value_type')
        length = body.get('length')

        if value_type == 'enum':
            value = json.dumps(value.split(','))

        cursor.execute('''
            INSERT INTO message_bodies (message_name, key, data_type, length, min, max, value,value_type)
            VALUES (?, ?, ?, ?, ?, ?,?,?)
        ''', (message_name, key, data_type, length, min_val, max_val, value, value_type))

    conn.commit()
    conn.close()
    return jsonify(new_message), 201


# 根据message_name更新消息
@app.route('/message/<string:id>', methods=['PUT'])
def update_message(id):
    new_message = request.get_json()
    message_name = new_message['message_name']
    descriptor = new_message.get('descriptor')
    descriptor = json.dumps(descriptor)
    message_bodies = new_message['message_bodies']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE messages
        SET descriptor = ?
        WHERE message_name = ?
    ''', (descriptor, message_name))

    cursor.execute('''
        DELETE FROM message_bodies
        WHERE message_name = ?
    ''', (message_name,))
    for body in message_bodies:
        key = body['key']
        data_type = body['data_type']
        min_val = body.get('min')
        max_val = body.get('max')
        value = body.get('value')
        value_type = body.get('value_type')
        length = body.get('length')

        if value_type == 'enum':
            value = json.dumps(value.split(','))

        cursor.execute('''
            INSERT INTO message_bodies (message_name, key, data_type, length, min, max, value,value_type)
            VALUES (?, ?, ?, ?, ?, ?,?,?)
        ''', (message_name, key, data_type, length, min_val, max_val, value, value_type))

    conn.commit()
    conn.close()
    return jsonify(new_message), 200


@app.route('/message/<string:id>', methods=['DELETE'])
def delete_message(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM messages WHERE message_name = ?', (id,))
    conn.execute('DELETE FROM message_bodies WHERE message_name = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204


@app.route('/message_body/<string:name>/<string:key>', methods=['DELETE'])
def delete_message_body(name, key):
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM message_bodies WHERE message_name = ? AND key = ?', (name, key))
    conn.commit()
    conn.close()
    return '', 204


@app.route('/data_type/<string:data_type>', methods=['DELETE'])
def delete_data_type(data_type):
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM data_types WHERE data_type = ?', (data_type,))
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

# 删除value_type


@app.route('/value_type/<string:value_type>', methods=['DELETE'])
def delete_value_type(value_type):
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM value_types WHERE value_type = ?', (value_type,))
    conn.commit()
    conn.close()
    return '', 204


@app.route('/value_types', methods=['GET'])
def get_value_types():
    conn = get_db_connection()
    value_types = conn.execute('SELECT value_type FROM value_types').fetchall()
    conn.close()
    return jsonify([row['value_type'] for row in value_types])


@app.route('/value_type', methods=['POST'])
def add_value_type():
    new_value_type = request.get_json()['value_type']
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO value_types (value_type)
            VALUES (?)
        ''', (new_value_type,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Value type already exists'}), 400
    conn.close()
    return '', 201


@app.route('/generate_code', methods=['GET'])
def generate_code():
    start_id = request.args.get('start_id', type=int)
    end_id = request.args.get('end_id', type=int)

    try:
        with get_db_connection() as conn:
            query = ""
            if start_id and end_id:
                query = f'''
                    SELECT id, message_id, message_name, message_type, message_size, descriptor 
                    FROM messages 
                    WHERE message_id BETWEEN {start_id} AND {end_id}
                '''
            elif start_id:
                query = f'''
                    SELECT id, message_id, message_name, message_type, message_size, descriptor 
                    FROM messages 
                    WHERE message_id >= {start_id}
                '''
            elif end_id:
                query = f'''
                    SELECT id, message_id, message_name, message_type, message_size, descriptor 
                    FROM messages 
                    WHERE message_id <= {end_id}
                '''
            else:
                query = '''
                    SELECT id, message_id, message_name, message_type, message_size, descriptor 
                    FROM messages 
                '''

            print(query)
            messages = conn.execute(query).fetchall()
            code_list = []

            message_names = [message['message_name'] for message in messages]
            function_define = buildFunctionDefine(message_names)
            function_routine = insertFunctionRoutine(message_names)

            for message in messages:
                message_name = message['message_name']
                message_id = message['message_id']
                message_size = message['message_size']
                descriptor = message['descriptor']
                if descriptor:
                    descriptor = json.loads(descriptor)

                message_bodies = conn.execute(
                    'SELECT key, data_type, length, min, max, value, value_type FROM message_bodies WHERE message_name = ?',
                    (message_name,)
                ).fetchall()
                bodies = [dict(body) for body in message_bodies]

                fields_info = {}
                for body in bodies:
                    key = body['key']
                    data_type = body['data_type']
                    value_type = body['value_type']
                    min_val = body.get('min')
                    max_val = body.get('max')
                    value = body.get('value')
                    length = body['length']

                    fields_info[key] = {
                        "length": length,
                        "type": data_type,
                        "subtype": value_type,
                        "min": min_val,
                        "max": max_val,
                        "value": value,
                    }

                    if value_type == "enum":
                        fields_info[key]["enums"] = json.loads(value)

                complicated_msg = ''
                if descriptor:
                    descriptorCount = len(descriptor)
                    complicated_msg = build_complicated_msg(
                        descriptorCount, descriptor)

                header = buildHeader(message_name, message_id, message_size)
                fields_info_str = build_fields(fields_info)
                footer = buildFooter()

                code = function_define + function_routine + header + \
                    complicated_msg + fields_info_str + footer
                code_list.append(code)

            return jsonify(code_list)
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    init_db()  # 在应用启动时初始化数据库
    app.run(debug=True)
