import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

def generate_base64(raw_data):
    """Fungsi untuk mengonversi data mentah ke Base64"""
    try:
        # Konversi string hexadecimal mentah ke bytes
        raw_bytes = bytes.fromhex(raw_data)
        # Encode bytes ke Base64
        base64_encoded = base64.b64encode(raw_bytes).decode('utf-8')
        return base64_encoded
    except ValueError:
        return None

@app.route('/generate_base64', methods=['POST'])
def generate_base64_endpoint():
    """Endpoint untuk menerima data mentah dan mengembalikan Base64"""
    data = request.get_json()
    raw_data = data.get('raw_data')

    if not raw_data:
        return jsonify({"error": "Data tidak ditemukan"}), 400

    # Generate Base64 dari data mentah
    base64_encoded = generate_base64(raw_data)
    if not base64_encoded:
        return jsonify({"error": "Format data tidak valid"}), 400

    return jsonify({"base64_data": base64_encoded})

if __name__ == '__main__':
    app.run(debug=True)
