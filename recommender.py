from storage import get_borrow_records, get_books

def recommend_books(user_name):
    records = get_borrow_records()
    books = get_books()

    # 获取用户借阅历史ID
    user_books = {r['book_id'] for r in records
                  if r['user'] == user_name and not r['returned']}

    # 推荐逻辑：排除已借阅，按库存降序
    return sorted(
        [b for b in books if b['id'] not in user_books and b['stock'] > 0],
        key=lambda x: x['stock'],
        reverse=True
    )[:5]  # 返回前5个推荐