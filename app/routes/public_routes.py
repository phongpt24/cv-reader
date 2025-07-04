# public_routes.py
import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory, current_app, render_template # Đảm bảo có render_template
from werkzeug.utils import secure_filename
from .. import database, gemini_service 
from pypdf import PdfReader 
from docx import Document 

# Tạo một Blueprint mới cho các route công khai
public_bp = Blueprint('public_bp', __name__)

def extract_text_from_file_path(file_path):
    """Trích xuất text từ file dựa trên đường dẫn."""
    file_extension = file_path.rsplit('.', 1)[1].lower()
    text = ""
    try:
        with open(file_path, 'rb') as f:
            if file_extension == 'pdf':
                reader = PdfReader(f)
                text = "".join(page.extract_text() or "" for page in reader.pages)
            elif file_extension == 'docx':
                document = Document(f)
                text = "\n".join(para.text for para in document.paragraphs)
            elif file_extension == 'txt':
                text = f.read().decode('utf-8')
            else:
                print(f"Định dạng file {file_extension} không được hỗ trợ để trích xuất văn bản.")
    except Exception as e:
        print(f"Lỗi khi đọc file {file_path}: {e}")
        return ""
    return text.strip()

@public_bp.route('/') # Route để phục vụ trang công khai
def public_jobs_page():
    return render_template('jobs.html')

@public_bp.route('/jobs', methods=['GET'])
def get_public_jobs_endpoint():
    try:
        jobs = database.get_all_job_postings(active_only=True)
        return jsonify(jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@public_bp.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply_for_job_endpoint(job_id):
    if 'file' not in request.files:
        return jsonify({"error": "Yêu cầu thiếu file CV."}), 400
    
    try:
        job_details = database.get_job_details(job_id)
        if not job_details:
            return jsonify({"error": "Không tìm thấy tin tuyển dụng."}), 404
        
        job_folder = job_details['cv_storage_folder']
        jd_text = job_details['job_description']

        file = request.files['file']
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        cv_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], job_folder, filename)
        file.save(cv_save_path)

        cv_text = extract_text_from_file_path(cv_save_path)
        if not cv_text:
            if os.path.exists(cv_save_path):
                os.remove(cv_save_path)
            return jsonify({"error": "File CV không có nội dung hoặc định dạng không được hỗ trợ."}), 400

        structured_data = gemini_service.get_structured_data_from_cv(cv_text)
        analysis_result = gemini_service.get_analysis_vs_jd(cv_text, jd_text)
        match_score = gemini_service.extract_match_score(analysis_result)

        personal_info = structured_data.get('personal_info', {})
        references_info = structured_data.get('references', []) # NEW: Get references

        database.add_candidate(
            job_id=job_id,
            full_name=personal_info.get('full_name', 'Chưa rõ'),
            email=personal_info.get('email'),
            phone=personal_info.get('phone_number'),
            cv_filename=filename, 
            match_score=match_score,
            structured_data=structured_data,
            analysis_result=analysis_result,
            references_data=references_info # NEW: Pass references
        )
        
        return jsonify({"message": "Nộp CV thành công! Cảm ơn bạn đã ứng tuyển."}), 201

    except Exception as e:
        if 'cv_save_path' in locals() and os.path.exists(cv_save_path):
            os.remove(cv_save_path)
        return jsonify({"error": f"Lỗi khi nộp CV: {str(e)}"}), 500

@public_bp.route('/download_cv/<job_folder>/<filename>', methods=['GET'])
def download_cv(job_folder, filename):
    """
    Tải file CV từ thư mục cụ thể của job.
    <job_folder> là thư mục UUID của job.
    <filename> là tên file CV.
    """
    try:
        directory_to_serve = os.path.join(current_app.config['UPLOAD_FOLDER'], job_folder)
        full_file_path_attempt = os.path.join(directory_to_serve, filename)

        print(f"DEBUG: UPLOAD_FOLDER = {current_app.config['UPLOAD_FOLDER']}") 
        print(f"DEBUG: Job Folder = {job_folder}") 
        print(f"DEBUG: Filename = {filename}") 
        print(f"DEBUG: Đang cố gắng tìm file tại: {full_file_path_attempt}") 

        return send_from_directory(
            directory_to_serve,
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        print(f"LỖI: File '{filename}' không tìm thấy trong thư mục '{directory_to_serve}'.")
        return jsonify({"error": "File CV không tìm thấy."}), 404
    except Exception as e:
        print(f"LỖI CHUNG KHI TẢI CV: {e}")
        return jsonify({"error": f"Lỗi máy chủ khi tải CV: {str(e)}"}), 500