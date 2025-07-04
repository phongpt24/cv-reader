import os
import uuid
import shutil # Thêm thư viện shutil để xóa thư mục
from flask import Blueprint, request, jsonify, current_app, render_template # Đảm bảo có render_template
from werkzeug.utils import secure_filename
from .. import database, gemini_service

# Tạo một Blueprint mới cho các route của nhà tuyển dụng
recruiter_bp = Blueprint('recruiter_bp', __name__)

@recruiter_bp.route('/') # Route để phục vụ trang nhà tuyển dụng
def recruiter_dashboard():
    return render_template('recruiter.html')

@recruiter_bp.route('/jobs', methods=['POST'])
def create_job_posting_endpoint():
    data = request.get_json()
    title = data.get('title')
    jd = data.get('jd')
    if not title or not jd:
        return jsonify({"error": "Tiêu đề và mô tả công việc không được để trống."}), 400

    try:
        # Gọi Gemini để tóm tắt JD
        jd_summary = gemini_service.get_summary_from_jd(jd)

        folder_name = str(uuid.uuid4())
        job_folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(job_folder_path, exist_ok=True)
        
        job_id = database.create_job_posting(title, jd, jd_summary, folder_name)
        return jsonify({"message": "Tạo tin tuyển dụng thành công.", "job_id": job_id}), 201
    except Exception as e:
        return jsonify({"error": f"Lỗi khi tạo tin tuyển dụng: {str(e)}"}), 500

@recruiter_bp.route('/jobs', methods=['GET'])
def get_recruiter_jobs_endpoint():
    try:
        jobs = database.get_all_job_postings(active_only=False)
        return jsonify(jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recruiter_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job_posting_endpoint(job_id):
    try:
        # Gọi hàm xóa từ database và nhận lại tên thư mục
        cv_folder_name = database.delete_job_posting(job_id)
        
        if cv_folder_name:
            # Xóa thư mục lưu trữ CV và tất cả nội dung bên trong
            job_folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cv_folder_name)
            if os.path.exists(job_folder_path):
                shutil.rmtree(job_folder_path) # Xóa toàn bộ thư mục và nội dung
                print(f"Đã xóa thư mục: {job_folder_path}")
            else:
                print(f"Thư mục không tồn tại: {job_folder_path}")
                
            return jsonify({"message": f"Tin tuyển dụng ID {job_id} và các dữ liệu liên quan đã được xóa thành công."}), 200
        else:
            return jsonify({"error": "Không tìm thấy tin tuyển dụng để xóa hoặc không xóa được."}), 404
    except Exception as e:
        return jsonify({"error": f"Lỗi khi xóa tin tuyển dụng: {str(e)}"}), 500

@recruiter_bp.route('/jobs/<int:job_id>/candidates', methods=['GET'])
def get_candidates_for_job_endpoint(job_id):
    try:
        candidates = database.get_candidates_for_job(job_id)
        job_details = database.get_job_details(job_id)
        response_data = {
            "candidates": candidates,
            "job_folder": job_details.get('cv_storage_folder') if job_details else None
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recruiter_bp.route('/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate_details_endpoint(candidate_id):
    try:
        candidate = database.get_candidate_details(candidate_id)
        if not candidate:
            return jsonify({"error": "Không tìm thấy ứng viên."}), 404
        return jsonify(candidate)
    except Exception as e:
        return jsonify({"error": f"{str(e)}"}), 500

@recruiter_bp.route('/candidates/<int:candidate_id>/status', methods=['PUT'])
def update_status_endpoint(candidate_id):
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({"error": "Trạng thái mới không được cung cấp."}), 400
    
    try:
        if database.update_candidate_status(candidate_id, new_status):
            return jsonify({"message": "Cập nhật trạng thái thành công."})
        else:
            return jsonify({"error": "Không tìm thấy ứng viên hoặc trạng thái không thay đổi."}), 404
    except Exception as e:
        return jsonify({"error": f"Lỗi khi cập nhật: {str(e)}"}), 500