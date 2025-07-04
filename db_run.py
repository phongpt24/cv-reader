import mysql.connector

# --- THÔNG TIN KẾT NỐI CSDL ---
# Cấu hình này phải khớp với MariaDB Docker container của bạn
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456', # Thay mật khẩu bạn đã đặt ở lệnh docker
    'database': 'cv_analysis_db'
}

def create_tables():
    """
    Kết nối đến cơ sở dữ liệu và tạo bảng 'job_postings' và 'candidates'.
    Trước tiên, các bảng sẽ được xóa nếu chúng đã tồn tại để đảm bảo môi trường sạch.
    """
    conn = None
    try:
        # Kết nối đến cơ sở dữ liệu
        print("Đang kết nối đến cơ sở dữ liệu...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Kết nối thành công.")

        
        # SQL để tạo bảng job_postings
        # Đã thêm cột 'jd_summary'
        create_job_postings_table_sql = """
        CREATE TABLE IF NOT EXISTS job_postings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            job_description TEXT NOT NULL,
            jd_summary TEXT NULL, -- Cột mới đã được thêm vào đây
            cv_storage_folder VARCHAR(255) NOT NULL UNIQUE, -- Thư mục lưu CV cho tin này
            start_date DATE,
            end_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # SQL để tạo bảng candidates
        # Bảng này có khóa ngoại liên kết với tin tuyển dụng
        # Đã thêm cột 'references_json' trực tiếp vào đây
        create_candidates_table_sql = """
        CREATE TABLE IF NOT EXISTS candidates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_posting_id INT NOT NULL, -- Khóa ngoại liên kết với tin tuyển dụng
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            phone_number VARCHAR(50),
            status ENUM('Mới', 'Đã xem', 'Phù hợp', 'Không phù hợp', 'Phỏng vấn') DEFAULT 'Mới',
            cv_file_path VARCHAR(512) NOT NULL, -- Tên file CV (đường dẫn tương đối)
            match_score INT, -- Điểm phù hợp (ví dụ: 85)
            structured_data_json JSON,
            analysis_result_text TEXT,
            references_json JSON NULL, -- Cột mới đã được thêm trực tiếp vào đây
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_posting_id) REFERENCES job_postings(id) ON DELETE CASCADE
        );
        """

        # Thực thi lệnh tạo bảng job_postings
        print("Đang tạo bảng 'job_postings'...")
        cursor.execute(create_job_postings_table_sql)
        conn.commit()
        print("Bảng 'job_postings' đã được tạo (hoặc đã tồn tại) thành công.")

        # Thực thi lệnh tạo bảng candidates
        # Đảm bảo bảng job_postings đã tồn tại trước khi tạo bảng candidates
        print("Đang tạo bảng 'candidates'...")
        cursor.execute(create_candidates_table_sql)
        conn.commit()
        print("Bảng 'candidates' đã được tạo (hoặc đã tồn tại) thành công.")
        
    except mysql.connector.Error as err:
        print(f"Lỗi cơ sở dữ liệu: {err}")
        if conn:
            conn.rollback() # Hoàn tác các thay đổi nếu có lỗi
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("Kết nối cơ sở dữ liệu đã đóng.")

if __name__ == '__main__':
    create_tables()
