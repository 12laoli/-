from storage import get_books, save_books, get_borrow_records, save_borrow_records
from datetime import datetime

def borrow_book(user_name, book_id):
    books = get_books()
    records = get_borrow_records()

    # 检查库存
    book = next((b for b in books if b['id'] == book_id), None)
    if not book or book['stock'] <= 0:
        return False, "图书库存不足"

    # 检查是否已借未还
    if any(r for r in records if r['user'] == user_name
           and r['book_id'] == book_id and not r['returned']):
        return False, "您已借阅该书未归还"

    # 更新库存
    book['stock'] -= 1
    save_books(books)

    # 添加借阅记录
    records.append({
        'user': user_name,
        'book_id': book_id,
        'borrow_date': datetime.now().isoformat(),
        'returned': False
    })
    save_borrow_records(records)
    return True, "借阅成功"

def return_book(user_name, book_id):
    records = get_borrow_records()
    books = get_books()

    # 查找未归还记录
    record = next((r for r in records
                  if r['user'] == user_name
                  and r['book_id'] == book_id
                  and not r['returned']), None)
    if not record:
        return False, "未找到借阅记录"

    # 更新记录状态
    record['returned'] = True
    record['return_date'] = datetime.now().isoformat()
    save_borrow_records(records)

    # 更新库存
    book = next(b for b in books if b['id'] == book_id)
    book['stock'] += 1
    save_books(books)
    return True, "归还成功"

def get_user_records(user_name):
    records = get_borrow_records()
    return [r for r in records if r['user'] == user_name]