from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health Check
    ---
    tags:
      - Health
    responses:
      200:
        description: API is healthy
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Educational Platform API is running'
    }), 200
