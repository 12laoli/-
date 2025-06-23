from storage import get_books, save_books

def add_book(title, book_id, stock):
    books = get_books()
    # 检查图书是否存在
    for book in books:
        if book['id'] == book_id:
            book['stock'] += int(stock)
            save_books(books)
            return False  # 已存在，更新库存
    # 新书添加
    books.append({
        'id': book_id,
        'title': title,
        'stock': int(stock)
    })
    save_books(books)
    return True  # 添加成功

def search_books(keyword):
    books = get_books()
    return [book for book in books
            if keyword.lower() in book['title'].lower() or keyword == book['id']]