from flask import Flask, request, jsonify
import base64
import uuid
import datetime
import time
import qrcode  # Pastikan Anda menginstal qrcode dengan pip install qrcode[pil]

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
def encode_tag(tag, value):
    # Jika tag tidak perlu dikonversi
    no_conversion_tags = ["5A", "4F", "9F25"]
    if tag in no_conversion_tags:
        # Kembalikan data tag apa adanya
        if isinstance(value, dict):  # Struktur bertingkat
            inner_data = ''.join(encode_tag(inner_tag, inner_value) for inner_tag, inner_value in value.items())
            length = len(inner_data) // 2  # Panjang dalam byte
            return f"{tag}{length:02X}{inner_data}"
        else:  # Nilai sederhana
            encoded_value = value.encode("utf-8").hex()
            length = len(encoded_value) // 2  # Panjang dalam byte
            return f"{tag}{length:02X}{encoded_value}"
    
    # Konversi data ke heksadesimal
    if isinstance(value, dict):  # Tag bertingkat
        inner_data = ''.join(encode_tag(inner_tag, inner_value) for inner_tag, inner_value in value.items())
        length = len(inner_data) // 2  # Panjang dalam byte
        return f"{tag}{length:02X}{inner_data}"
    else:  # Nilai sederhana
        encoded_value = value.encode("utf-8").hex()
        length = len(encoded_value) // 2  # Panjang dalam byte
        return f"{tag}{length:02X}{encoded_value}"

# Contoh untuk menangani Tag yang Dikelompokkan dengan Informasi Panjang
def encode_grouped_tag(tag, nested_tags):
    """
    Mengkodekan tag yang dikelompokkan (seperti Tag 63) dengan menghitung panjang anak tag dan menambahkan informasi panjang.
    :param tag: Tag utama (misalnya, "63").
    :param nested_tags: Dictionary tag yang dikelompokkan.
    :return: Tag yang sudah dikodekan dengan informasi panjang.
    """
    # Pertama, hitung total panjang dari tag anak
    nested_data = ''.join(encode_tag(inner_tag, inner_value) for inner_tag, inner_value in nested_tags.items())
    total_length = len(nested_data) // 2  # Panjang dalam byte
    
    # Konversi panjang ke format heksadesimal
    length_hex = f"{total_length:02X}"
    
    # Kembalikan tag yang dikelompokkan dengan informasi panjang
    return f"{tag}{length_hex}{nested_data}"

# Data Contoh
tags = {
    "85": "CPV01",
    "61": {
        "4F": "A0000006022020",  # Ini dilewatkan untuk konversi
        "50": "QRISCPM",
    },
    "5A": "9360083039999999995F",  # Ini dilewatkan untuk konversi
    "5F20": "Niko Joanto",
    "5F2D": "iden",
    "5F50": "mailto:niko@yodu.id",
    "9F08": "3.1.2",
    "9F25": "8888",  # Ini dilewatkan untuk konversi
    "63": {  # Tag yang dikelompokkan
        "9F74": "b52765ca5127fec9c3430d5d01cd3453",
    },
}

# Memproses tag untuk menghasilkan output akhir
encoded_tags = ''.join(encode_tag(tag, value) for tag, value in tags.items())

# Penanganan khusus untuk tag yang dikelompokkan (misalnya, 63)
encoded_tags = encode_grouped_tag("63", tags["63"])

print(f"Tag yang sudah dikodekan dengan informasi panjang: {encoded_tags}")

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


# Generate QR with Timestamp
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

def validate_qr_code_with_timestamp(qr_data, time_count=120):
    """
    Validasi QR Code untuk memastikan masih berlaku (2 menit).
    :param qr_data: Data QR Code yang dipindai (termasuk timestamp).
    :return: True jika valid, False jika expired.
    """
    if 'timestamp' not in qr_data:
        raise ValueError("QR Code tidak memiliki timestamp.")
    
    current_time = int(time.time())
    time_diff = current_time - qr_data['timestamp']
    
    if time_diff > time_count:  # Cek jika lebih dari 120 detik
        print("QR Code telah kedaluwarsa.")
        return False
    
    print("QR Code masih berlaku.")
    return True
# Fungsi untuk mengonversi Hex menjadi Base64
def hex_to_base64(hex_data):
    # Pertama, hapus semua spasi dalam data hex
    hex_data = hex_data.replace(" ", "")
    
    # Pastikan data hex memiliki format yang benar (harus dalam bentuk byte)
    hex_bytes = bytes.fromhex(hex_data)
    
    # Konversi data hex yang sudah diubah menjadi Base64 menggunakan RFC 4648
    base64_data = base64.b64encode(hex_bytes).decode('utf-8')
    
    return base64_data

# Data Tag yang sudah dikodekan (hex) sebelumnya
encoded_tags = '8543505630316107A0000006022020500751524390036534E696B6F204A6F616E746F6964656E69646D61696C746F3A6E696B6F40796F64752E6964332E312E329F2588886305352363563363531323766666339333433306435643031636433343533'

# Konversi Hex menjadi Base64
base64_result = hex_to_base64(encoded_tags)

print(f"Base64 Data: {base64_result}")


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
        "timestamp": timestamp,
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
