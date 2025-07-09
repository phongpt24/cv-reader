import os
import google.generativeai as genai
import json
import re  # Thêm thư viện regex

# --- CẤU HÌNH API KEY ---
# CẢNH BÁO: Không lưu API Key trực tiếp trong code ở môi trường production.
# Hãy dùng biến môi trường: os.environ.get("GEMINI_API_KEY")
GEMINI_API_KEY = "AIzaSyB8sYvVZ9fgOXvZ8B_INXVOU2WZFC3JrYc"  # Thay bằng API Key của bạn

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY không được thiết lập.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_summary_from_jd(jd_text: str) -> str:
    """
    Tạo prompt và gọi Gemini API để tóm tắt một JD.
    Trả về một bản tóm tắt ngắn gọn, tập trung vào các ý chính.
    """
    prompt = f"""
    Bạn là một chuyên gia tuyển dụng. Hãy đọc Mô tả Công việc (JD) dưới đây và tóm tắt lại các ý chính quan trọng nhất thành một danh sách ngắn gọn (3-5 gạch đầu dòng).
    Tập trung vào:
    - Trách nhiệm chính.
    - Yêu cầu cốt lõi (kinh nghiệm, kỹ năng).
    - Quyền lợi nổi bật.

    Mô tả Công việc (JD):
    ---
    {jd_text}
    ---

    Bản tóm tắt:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi khi tóm tắt JD bằng Gemini: {e}")
        # Trả về một phần của JD gốc nếu có lỗi
        return (jd_text[:250] + '...') if len(jd_text) > 250 else jd_text


def get_analysis_vs_jd(cv_text: str, jd_text: str) -> str:
    """
    Tạo prompt và gọi Gemini API để phân tích, so sánh CV với JD.
    Trả về kết quả dạng text thô.
    """
    prompt = f"""
    Bạn là một Trợ lý Tuyển dụng AI chuyên gia. Nhiệm vụ của bạn là đánh giá một CV dựa trên một Mô tả Công việc (JD).
    Hãy thực hiện các yêu cầu sau và trình bày kết quả theo đúng định dạng được yêu cầu.

    **ĐẦU VÀO:**
    1.  **Mô tả Công việc (JD):**\n---\n{jd_text}\n---
    2.  **Nội dung CV:**\n---\n{cv_text}\n---

    **YÊU CẦU ĐẦU RA (Sử dụng chính xác các tiêu đề sau):**

    **[TÓM TẮT CV]**
    (Tóm tắt CV trong 3-5 câu.)

    **[PHÂN TÍCH MỨC ĐỘ PHÙ HỢP VỚI JD]**
    (Phân tích chi tiết điểm mạnh và điểm yếu của CV so với JD.)

    **[ĐIỂM TƯƠNG THÍCH]**
    (Đưa ra một con số phần trăm, ví dụ: 85%. Giải thích ngắn gọn tại sao bạn đưa ra con số đó.)

    **[ĐÁNH GIÁ TỔNG QUAN VÀ ĐỀ XUẤT]**
    (Đưa ra nhận định cuối cùng và đề xuất bước tiếp theo, ví dụ: "Rất phù hợp, đề xuất phỏng vấn".)
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {e}")
        raise

def get_structured_data_from_cv(cv_text: str) -> dict:
    """
    Tạo prompt và gọi Gemini API để trích xuất thông tin có cấu trúc từ CV.
    Trả về một đối tượng dict đã được parse.
    """
    prompt = f"""
    Bạn là một trợ lý AI chuyên về trích xuất dữ liệu chính xác.
    Nhiệm vụ của bạn là đọc nội dung của một CV và trích xuất thông tin vào một cấu trúc JSON định sẵn.
    QUY TẮC:
    - Chỉ trả về duy nhất một đối tượng JSON hợp lệ.
    - Không thêm bất kỳ văn bản giải thích nào trước hoặc sau đối tượng JSON.
    - Nếu không tìm thấy thông tin, hãy sử dụng giá trị `null`.

    CẤU TRÚC JSON CẦN TRẢ VỀ:
    {{
      "personal_info": {{ "full_name": "string", "age": "string", "email": "string", "phone_number": "string", "address": "string", "linkedin_url": "string | null", "portfolio_url": "string | null" }},
      "summary": "string | null",
      "work_experience": [ {{ "company_name": "string", "position": "string", "start_date": "string", "end_date": "string | 'Present'", "responsibilities": ["string"] }} ],
      "education": [
        {{
          "institution_name": "string",
          "degree": "string",
          "major": "string",
          "graduation_year": "string | number",
          "gpa": "number | string | null",
          "thesis_project": "string | null"
        }}
      ],
      "skills": {{ "technical": ["string"], "soft": ["string"] }},
      "certifications": [ {{ "name": "string", "issuing_organization": "string", "year": "string | number | null" }} ],
      "languages": [ {{ "language": "string", "proficiency": "string" }} ],
      "references": [ {{ "name": "string", "title": "string | null", "company": "string | null", "contact": "string | null" }} ]
    }}

    NỘI DUNG CV CẦN TRÍCH XUẤT:
    ---
    {cv_text}
    ---
    """
    try:
        response = model.generate_content(prompt)
        ai_response_text = response.text
        
        if ai_response_text.strip().startswith("```json"):
            ai_response_text = ai_response_text.strip()[7:-4]
            
        return json.loads(ai_response_text)
    except json.JSONDecodeError as e:
        print(f"Lỗi giải mã JSON từ AI: {e}\nResponse thô: {ai_response_text}")
        raise ValueError("AI không trả về JSON hợp lệ.")
    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {e}")
        raise

def extract_match_score(analysis_text: str) -> int:
    """
    Sử dụng regex để tìm và trích xuất điểm số (dạng số) từ văn bản phân tích.
    """
    if not analysis_text:
        return 0
        
    match = re.search(r'\[ĐIỂM TƯƠNG THÍCH\][^\[]*?(\d+)\s*%', analysis_text)
    if match:
        return int(match.group(1))
    return 0