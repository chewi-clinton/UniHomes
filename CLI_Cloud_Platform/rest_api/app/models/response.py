from flask import jsonify

def success_response(data=None, message="Success"):
    return jsonify({
        "success": True,
        "data": data,
        "message": message
    })

def error_response(message, status_code=None):
    response = jsonify({
        "success": False,
        "error": message
    })
    if status_code:
        response.status_code = status_code
    return response