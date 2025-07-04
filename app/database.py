# database.py
import mysql.connector
import json

# --- THÔNG TIN KẾT NỐI CSDL ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456', # <-- Cần thay thế bằng mật khẩu của bạn
    'database': 'cv_analysis_db'
}

def get_db_connection():
    """Tạo và trả về một kết nối CSDL."""
    return mysql.connector.connect(**DB_CONFIG)

# === HÀM QUẢN LÝ TIN TUYỂN DỤNG (Job Postings) ===

def create_job_posting(title, jd, jd_summary, folder_name, start_date=None, end_date=None):
    """Thêm tin tuyển dụng mới."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO job_postings (title, job_description, jd_summary, cv_storage_folder, start_date, end_date)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (title, jd, jd_summary, folder_name, start_date, end_date))
    conn.commit()
    job_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return job_id

def get_all_job_postings(active_only=False):
    """Lấy danh sách tin tuyển dụng."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if active_only:
        # Lấy thêm job_description đầy đủ để có thể hiển thị khi người dùng nhấp vào
        query = "SELECT id, title, job_description FROM job_postings WHERE is_active = TRUE AND (end_date IS NULL OR end_date >= CURDATE()) ORDER BY created_at DESC"
        cursor.execute(query)
    else:
        # Dành cho nhà tuyển dụng xem tất cả
        query = "SELECT id, title, start_date, end_date, is_active FROM job_postings ORDER BY created_at DESC"
        cursor.execute(query)
    
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jobs
    
def get_job_details(job_id):
    """Lấy chi tiết một tin tuyển dụng."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM job_postings WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    cursor.close()
    conn.close()
    return job

def delete_job_posting(job_id):
    """
    Xóa tin tuyển dụng và trả về tên thư mục CV liên quan.
    Nếu không tìm thấy job, trả về None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Lấy tên thư mục trước khi xóa
        cursor.execute("SELECT cv_storage_folder FROM job_postings WHERE id = %s", (job_id,))
        folder_name_row = cursor.fetchone()
        
        if not folder_name_row:
            return None # Job không tồn tại
            
        cv_folder_name = folder_name_row[0]

        # Xóa các ứng viên liên quan trước
        cursor.execute("DELETE FROM candidates WHERE job_posting_id = %s", (job_id,))
        
        # Sau đó xóa tin tuyển dụng
        cursor.execute("DELETE FROM job_postings WHERE id = %s", (job_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return cv_folder_name
        else:
            return None # Job không tồn tại hoặc không xóa được
    except Exception as e:
        conn.rollback() # Hoàn tác nếu có lỗi
        print(f"Lỗi khi xóa tin tuyển dụng: {e}")
        raise # Ném lỗi để xử lý ở tầng cao hơn
    finally:
        cursor.close()
        conn.close()

# === HÀM QUẢN LÝ ỨNG VIÊN (Candidates) ===

def add_candidate(job_id, full_name, email, phone, cv_filename, match_score, structured_data, analysis_result, references_data):
    """Thêm một ứng viên mới đã được phân tích."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO candidates 
    (job_posting_id, full_name, email, phone_number, cv_file_path, match_score, structured_data_json, analysis_result_text, references_json) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    structured_data_str = json.dumps(structured_data, ensure_ascii=False) if structured_data else None
    references_data_str = json.dumps(references_data, ensure_ascii=False) if references_data else None # NEW LINE
    
    cursor.execute(query, (job_id, full_name, email, phone, cv_filename, match_score, structured_data_str, analysis_result, references_data_str)) # UPDATED LINE
    conn.commit()
    candidate_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return candidate_id

def get_candidates_for_job(job_id):
    """Lấy danh sách ứng viên cho một tin tuyển dụng."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, full_name, email, status, match_score, cv_file_path FROM candidates WHERE job_posting_id = %s ORDER BY match_score DESC"
    cursor.execute(query, (job_id,))
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    return candidates

def get_candidate_details(candidate_id):
    """Lấy chi tiết thông tin của một ứng viên."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM candidates WHERE id = %s"
    cursor.execute(query, (candidate_id,))
    candidate = cursor.fetchone()
    cursor.close()
    conn.close()

    if candidate and candidate.get('structured_data_json'):
        candidate['structured_data_json'] = json.loads(candidate['structured_data_json'])
    # NEW: Load references_json
    if candidate and candidate.get('references_json'):
        candidate['references_json'] = json.loads(candidate['references_json'])
        
    return candidate

def update_candidate_status(candidate_id, new_status):
    """Cập nhật trạng thái của một ứng viên."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE candidates SET status = %s WHERE id = %s"
    cursor.execute(query, (new_status, candidate_id))
    conn.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    conn.close()
    return affected_rows > 0