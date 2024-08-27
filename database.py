import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 创建消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            key TEXT NOT NULL,
            data_type TEXT NOT NULL,
            min Real,
            max Real,
            value Real
        )
    ''')

    # 创建数据类型表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL UNIQUE
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()