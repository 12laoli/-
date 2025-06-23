import json
import os

def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_data(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# 图书数据操作
def get_books():
    return load_data('data/books.json')

def save_books(books):
    save_data(books, 'data/books.json')

# 用户数据操作
def get_users():
    return load_data('data/users.json')

def save_users(users):
    save_data(users, 'data/users.json')

# 借阅记录操作
def get_borrow_records():
    return load_data('data/borrow_records.json')

def save_borrow_records(records):
    save_data(records, 'data/borrow_records.json')