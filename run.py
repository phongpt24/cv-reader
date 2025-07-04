from app import create_app
from db_run import create_tables # Import hàm create_tables từ db_run.py

if __name__ == '__main__':
    # Gọi hàm tạo bảng trước khi khởi chạy ứng dụng Flask
    print("Đang khởi tạo cơ sở dữ liệu...")
    create_tables()


    # Tạo một instance của ứng dụng Flask từ factory function
    app = create_app()

    # Chạy ứng dụng với chế độ debug
    # Trong production, bạn nên dùng một WSGI server như Gunicorn hoặc Waitress
    app.run(debug=True, port=5000)
