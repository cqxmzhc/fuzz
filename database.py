import sqlite3


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 创建消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            message_name TEXT UNIQUE NOT NULL,
            message_type TEXT NOT NULL
        )
    ''')

    # 创建消息体表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_bodies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_name TEXT NOT NULL,
            key TEXT NOT NULL,
            data_type TEXT NOT NULL,
            value_type TEXT NOT NULL,
            min Real,
            max Real,
            value Real,
            descriptor TEXT,
            FOREIGN KEY (message_name) REFERENCES messages (message_name)
        )
    ''')

    # 创建数据类型表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL UNIQUE
        )
    ''')

    # 创建值类型表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS value_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value_type TEXT NOT NULL UNIQUE
        )
    ''')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
