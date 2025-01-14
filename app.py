from flask import Flask, request, jsonify
import base64
import uuid
import datetime

app = Flask(__name__)

# Validate Input
def validate_input(data):
    required_fields = ['user_account_number', 'device_id', 'device_model', 'os_version', 'app_version', 'ip_address_public']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing or empty field: {field}"
    return True, None

# Generate UUID and Secret Key
def generate_yodu_ref_no():
    return str(uuid.uuid4())

def generate_secret_key():
    return base64.b64encode(uuid.uuid4().bytes).decode('utf-8')

# Get User Data
def get_data_user(user_account_number):
    return {
        "name": "Riki Derian",
        "account_number": user_account_number,
        "balance": 1000000
    }

# Encode tags recursively
def encode_tag(tag, value):
    if isinstance(value, dict):  # Nested tag
        inner_data = ''.join(encode_tag(inner_tag, inner_value) for inner_tag, inner_value in value.items())
        length = len(inner_data) // 2  # Length in bytes
        return f"{tag}{length:02X}{inner_data}"
    else:  # Simple value
        encoded_value = value.encode("utf-8").hex()
        length = len(encoded_value) // 2  # Length in bytes
        return f"{tag}{length:02X}{encoded_value}"
def luhn_check_digit(base_data):
    """
    Hitung check digit menggunakan algoritma Luhn.
    :param base_data: String 18 digit (BIN + Sumber Dana + NoCustomer)
    :return: Check digit (1 digit)
    """
    digits = [int(d) for d in base_data]
    # Lakukan operasi Luhn pada digit
    for i in range(len(digits) - 1, -1, -2):  # Mulai dari posisi ganjil (0-based index)
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    total = sum(digits)
    return (10 - (total % 10)) % 10  # Check digit


def process_tag_5a(bin_nns, source_fund, customer_number, tags):
    """
    Proses Tag 5A berdasarkan aturan yang diberikan.
    :param bin_nns: BIN berbasis NNS (6 digit)
    :param source_fund: Sumber Dana (4 digit)
    :param customer_number: Nomor Customer (8 digit)
    :param tags: Dictionary berisi semua tag dalam QR Code
    :return: Updated dictionary dengan Tag 5A jika diperlukan
    """
    if "57" not in tags:  # Jika Tag 57 tidak ada
        # Gabungkan base data
        base_data = f"{bin_nns}{source_fund}{customer_number}"
        if len(base_data) != 18:
            raise ValueError("Base data harus 18 digit (BIN + Sumber Dana + NoCustomer)")

        # Hitung check digit
        check_digit = luhn_check_digit(base_data)

        # Tambahkan check digit ke base data
        full_pan = f"{base_data}{check_digit}"

        # Tambahkan Tag 5A ke tags
        tags["5A"] = full_pan

    return tags


# Contoh penggunaan
bin_nns = "936008"  # BIN berbasis NNS (6 digit)
source_fund = "3030"  # Sumber Dana (4 digit)
customer_number = "99999999"  # NoCustomer (8 digit)

# Tags awal (contoh tanpa Tag 57)
tags = {
    "85": "CPV01",
    "61": {
        "4F": "A0000006022020",
        "50": "QRISCPM"
    }
}

# Proses Tag 5A
updated_tags = process_tag_5a(bin_nns, source_fund, customer_number, tags)

# Cetak hasil
print("Tags setelah diproses:", updated_tags)
def generate_qr_with_timestamp(data):
    """
    Membuat QR Code dengan timestamp.
    :param data: Data utama untuk QR Code.
    :return: QR Code dengan timestamp.
    """
    # Tambahkan timestamp (UNIX timestamp dalam detik)
    timestamp = int(time.time())
    qr_data = {
        "data": data,
        "timestamp": timestamp
    }
    
    # Buat QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Simpan QR Code ke file
    img = qr.make_image(fill="black", back_color="white")
    img.save("qr_code_with_timestamp.png")
    
    print(f"QR Code dibuat dengan timestamp: {timestamp}")
    return qr_data

def validate_qr_code_with_timestamp(qr_data, creation_time, time_count):
    """
    Validasi QR Code untuk memastikan masih berlaku (2 menit).
    :param qr_data: Data QR Code yang dipindai (termasuk timestamp).
    :return: True jika valid, False jika expired.
    """
    current_time = int(time.time())
    if current_time - creation_time > time_count:
    # Waktu sekarang (UNIX timestamp)
        print("QR Code telah kedaluwarsa.")  
        return False
    
    if not timestamp:
        raise ValueError("QR Code tidak memiliki timestamp.")
    
    # Hitung selisih waktu (dalam detik)
    time_diff = current_time - timestamp
    if time_diff > 120:  # 2 menit = 120 detik
        print("QR Code telah kedaluwarsa.")
        return False
    
    print("QR Code masih berlaku.")
    return True



# Generate QR CPM
@app.route('/generate_qr_cpm', methods=['POST'])
def generate_qr_cpm():
    data = request.json

    # Step 1: Validate Input
    is_valid, error_message = validate_input(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # Step 2: Generate Yodu Ref No and Secret Key
    yodu_ref_no = generate_yodu_ref_no()
    secret_key = generate_secret_key()
    time_count = 120

    # Step 3: Set Validity Period (2 minutes from now)
    validity_period = datetime.datetime.utcnow() + datetime.timedelta(minutes=2)
    timestamp = int(validity_period.timestamp())

    # Step 4: Get User Data
    user_data = get_data_user(data['user_account_number'])

    # Step 5: Prepare Raw Tags
    raw_tags = {
        "85": "CPV01",
        "61": {
            "4F": "A0000006022020",
            "50": "QRISCPM",
            "5A": user_data["account_number"][:10] + "9360091430054667488F",
            "5F20": user_data["name"],
            "5F2D": "iden",
            "5F50": data["ip_address_public"],
            "9F08": data["app_version"],
            "9F25": user_data["account_number"][-4:],
            "61": f"{data['device_id']};{data['device_model']};{data['os_version']}",
            "63": {
                "9F74": "cheque:32134296447056921766"
            }
        }
    }

    # Step 6: Encode Tags
    encoded_tags = ''.join(encode_tag(tag, value) for tag, value in raw_tags.items())

    # Step 7: Convert HEX to Binary
    binary_data = bytes.fromhex(encoded_tags)

    # Step 8: Convert Binary to Base64
    base64_data = base64.b64encode(binary_data).decode("utf-8")
    

    # Step 9: Return Base64 Data
    return jsonify({
        "yodu_ref_no": yodu_ref_no,
        "secret_key": secret_key,
        "validity_period": validity_period.isoformat(),
        "base64_qr_cpm": base64_data,
        "time_count": time_count

    }), 200

if __name__ == '__main__':
    app.run(debug=True)
