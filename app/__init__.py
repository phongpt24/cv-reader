import os
from flask import Flask
from flask_cors import CORS

def create_app():
    """
    Factory function để tạo và cấu hình ứng dụng Flask.
    """
    app = Flask(__name__)
    CORS(app)

    # Cấu hình thư mục upload
    # Đường dẫn tuyệt đối để đảm bảo hoạt động ổn định
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Import và đăng ký Blueprints từ các file routes
    from .routes.recruiter_routes import recruiter_bp
    from .routes.public_routes import public_bp

    # Đăng ký Blueprint với tiền tố URL
    # Tất cả các route trong recruiter_bp sẽ có dạng /recruiter/...
    app.register_blueprint(recruiter_bp, url_prefix='/recruiter')
    
    # Tất cả các route trong public_bp sẽ có dạng /public/...
    app.register_blueprint(public_bp, url_prefix='/public')

    return app