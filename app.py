from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import traceback

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据存储文件路径
BOOKS_FILE = 'books.json'
BORROW_RECORDS_FILE = 'borrow_records.json'

# 初始化数据文件
def init_data_files():
    for file_path in [BOOKS_FILE, BORROW_RECORDS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)

# 加载数据
def load_data(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"加载数据错误: {str(e)}")
        traceback.print_exc()
        return []

# 保存数据
def save_data(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"保存数据错误: {str(e)}")
        traceback.print_exc()
        return False

# ========== API端点定义 ==========

# 统一API响应格式
def api_response(success=True, message="操作成功", data=None, status_code=200):
    response = {
        "success": success,
        "code": status_code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(response), status_code

# 统一错误处理
@app.errorhandler(400)
def bad_request(error):
    return api_response(False, "请求参数错误", None, 400)

@app.errorhandler(404)
def not_found(error):
    return api_response(False, "资源未找到", None, 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return api_response(False, "请求方法不允许", None, 405)

@app.errorhandler(500)
def internal_server_error(error):
    return api_response(False, "服务器内部错误", None, 500)

# 主页
@app.route('/')
def home():
    return render_template('index.html')

# 获取所有图书
@app.route('/api/books', methods=['GET'])
def get_books_api():
    try:
        books = load_data(BOOKS_FILE)
        return api_response(data=books)
    except Exception as e:
        return api_response(False, f"获取图书列表失败: {str(e)}", None, 500)

# 添加图书
@app.route('/api/books', methods=['POST'])
def add_book_api():
    try:
        data = request.get_json()

        # 验证请求数据
        if not data or 'id' not in data or 'title' not in data or 'stock' not in data:
            return api_response(False, "缺少必要参数(id, title, stock)", None, 400)

        # 验证库存为整数
        try:
            stock = int(data['stock'])
            if stock < 0:
                return api_response(False, "库存不能为负数", None, 400)
        except ValueError:
            return api_response(False, "库存必须是整数", None, 400)

        books = load_data(BOOKS_FILE)

        # 检查图书是否已存在
        existing_book = next((b for b in books if b['id'] == data['id']), None)

        if existing_book:
            # 更新库存
            existing_book['stock'] += stock
            message = "图书库存更新成功"
        else:
            # 添加新书
            books.append({
                'id': data['id'],
                'title': data['title'],
                'stock': stock
            })
            message = "图书添加成功"

        if save_data(books, BOOKS_FILE):
            return api_response(message=message)
        else:
            return api_response(False, "保存图书数据失败", None, 500)

    except Exception as e:
        return api_response(False, f"添加图书失败: {str(e)}", None, 500)

# 搜索图书
@app.route('/api/books/search', methods=['GET'])
def search_books_api():
    try:
        query = request.args.get('q', '').strip().lower()
        books = load_data(BOOKS_FILE)

        if not query:
            return api_response(data=books)

        results = [
            b for b in books
            if query in b['title'].lower() or query == b['id']
        ]

        return api_response(data=results)
    except Exception as e:
        return api_response(False, f"搜索图书失败: {str(e)}", None, 500)

# 借阅图书
@app.route('/api/borrow', methods=['POST'])
def borrow_book_api():
    try:
        data = request.get_json()

        # 验证请求数据
        if not data or 'user' not in data or 'book_id' not in data:
            return api_response(False, "缺少必要参数(user, book_id)", None, 400)

        if not data['user'].strip():
            return api_response(False, "用户名不能为空", None, 400)

        books = load_data(BOOKS_FILE)
        records = load_data(BORROW_RECORDS_FILE)

        # 查找图书
        book = next((b for b in books if b['id'] == data['book_id']), None)

        if not book:
            return api_response(False, "图书不存在", None, 404)

        if book['stock'] <= 0:
            return api_response(False, "图书库存不足", None, 400)

        # 检查用户是否已借阅该书未归还
        existing_borrow = next((
            r for r in records
            if r['user'] == data['user']
            and r['book_id'] == data['book_id']
            and not r['returned']
        ), None)

        if existing_borrow:
            return api_response(False, "您已借阅该书且尚未归还", None, 400)

        # 减少库存
        book['stock'] -= 1

        # 添加借阅记录
        records.append({
            'user': data['user'],
            'book_id': data['book_id'],
            'book_title': book['title'],
            'borrow_date': datetime.now().isoformat(),
            'returned': False,
            'return_date': None
        })

        # 保存数据
        books_saved = save_data(books, BOOKS_FILE)
        records_saved = save_data(records, BORROW_RECORDS_FILE)

        if books_saved and records_saved:
            return api_response(message="借阅成功")
        else:
            return api_response(False, "保存借阅数据失败", None, 500)

    except Exception as e:
        return api_response(False, f"借阅图书失败: {str(e)}", None, 500)

# 归还图书
@app.route('/api/return', methods=['POST'])
def return_book_api():
    try:
        data = request.get_json()

        # 验证请求数据
        if not data or 'user' not in data or 'book_id' not in data:
            return api_response(False, "缺少必要参数(user, book_id)", None, 400)

        books = load_data(BOOKS_FILE)
        records = load_data(BORROW_RECORDS_FILE)

        # 查找未归还的记录
        record = next((
            r for r in records
            if r['user'] == data['user']
            and r['book_id'] == data['book_id']
            and not r['returned']
        ), None)

        if not record:
            return api_response(False, "未找到未归还的借阅记录", None, 404)

        # 更新记录
        record['returned'] = True
        record['return_date'] = datetime.now().isoformat()

        # 增加库存
        book = next((b for b in books if b['id'] == data['book_id']), None)
        if book:
            book['stock'] += 1

        # 保存数据
        books_saved = save_data(books, BOOKS_FILE)
        records_saved = save_data(records, BORROW_RECORDS_FILE)

        if books_saved and records_saved:
            return api_response(message="归还成功")
        else:
            return api_response(False, "保存归还数据失败", None, 500)

    except Exception as e:
        return api_response(False, f"归还图书失败: {str(e)}", None, 500)

# 获取借阅记录
@app.route('/api/borrow/list', methods=['GET'])
def get_borrow_list_api():
    try:
        user = request.args.get('user', '').strip()

        if not user:
            return api_response(False, "缺少用户参数", None, 400)

        records = load_data(BORROW_RECORDS_FILE)

        # 筛选该用户未归还的记录
        user_records = [
            r for r in records
            if r['user'] == user and not r['returned']
        ]

        return api_response(data=user_records)
    except Exception as e:
        return api_response(False, f"获取借阅记录失败: {str(e)}", None, 500)

# 获取推荐图书
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations_api():
    try:
        books = load_data(BOOKS_FILE)
        records = load_data(BORROW_RECORDS_FILE)

        # 获取最近30天内的借阅记录
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_borrow_ids = []

        for r in records:
            # 跳过没有借阅日期的记录
            if 'borrow_date' not in r:
                continue

            borrow_date = datetime.fromisoformat(r['borrow_date'])
            # 检查是否在最近30天内
            if borrow_date > thirty_days_ago:
                recent_borrow_ids.append(r['book_id'])

        # 统计借阅次数
        borrow_counts = {}
        for book_id in recent_borrow_ids:
            borrow_counts[book_id] = borrow_counts.get(book_id, 0) + 1

        # 推荐算法：库存充足且最近被借阅过的图书
        recommendations = [
            b for b in books
            if b['id'] in borrow_counts and b['stock'] > 5
        ]

        # 按借阅次数排序
        recommendations.sort(key=lambda x: borrow_counts[x['id']], reverse=True)

        return api_response(data=recommendations[:5])  # 返回前5本推荐书籍
    except Exception as e:
        # 出错时返回简单的推荐
        print(f"推荐算法出错: {str(e)}")
        books = load_data(BOOKS_FILE)
        simple_recs = [b for b in books if b['stock'] > 5][:5]
        return api_response(data=simple_recs)

# ========== 初始化数据并启动应用 ==========
def init_sample_data():
    """初始化示例数据"""
    # 初始化图书数据
    books = load_data(BOOKS_FILE)
    if not books:
        books = [
            {"id": "B001", "title": "Python编程从入门到实践", "stock": 15},
            {"id": "B002", "title": "JavaScript高级程序设计", "stock": 8},
            {"id": "B003", "title": "Flask Web开发实战", "stock": 3},
            {"id": "B004", "title": "深入理解计算机系统", "stock": 12},
            {"id": "B005", "title": "算法导论", "stock": 7},
            {"id": "B006", "title": "数据结构与算法分析", "stock": 9},
            {"id": "B007", "title": "机器学习实战", "stock": 6},
            {"id": "1", "title": "道德经", "stock": 0},
            {"id": "8", "title": "海底两万里", "stock": 3}
        ]
        save_data(books, BOOKS_FILE)

    # 初始化借阅记录
    records = load_data(BORROW_RECORDS_FILE)
    if not records:
        records = [
            {
                "user": "user1",
                "book_id": "B001",
                "book_title": "Python编程从入门到实践",
                "borrow_date": (datetime.now() - timedelta(days=5)).isoformat(),
                "returned": False,
                "return_date": None
            },
            {
                "user": "user2",
                "book_id": "B002",
                "book_title": "JavaScript高级程序设计",
                "borrow_date": (datetime.now() - timedelta(days=3)).isoformat(),
                "returned": True,
                "return_date": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "user": "user3",
                "book_id": "B004",
                "book_title": "深入理解计算机系统",
                "borrow_date": (datetime.now() - timedelta(days=10)).isoformat(),
                "returned": False,
                "return_date": None
            },
            {
                "user": "李知远",
                "book_id": "1",
                "book_title": "道德经",
                "borrow_date": "2025-06-19T22:39:21.444117",
                "returned": False,
                "return_date": None
            }
        ]
        save_data(records, BORROW_RECORDS_FILE)

if __name__ == '__main__':
    # 确保数据文件存在
    init_data_files()

    # 初始化示例数据
    init_sample_data()

    # 打印已注册的路由用于调试
    print("已注册的路由:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.methods} {rule}")

    # 启动服务器
    app.run(debug=True, port=5000, use_reloader=False)