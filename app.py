from flask import Flask, request, jsonify
import base64
import uuid
import datetime
import random
import string
import time
import qrcode  # Pastikan Anda menginstal qrcode dengan pip install qrcode[pil]

app = Flask(__name__)  # Inisialisasi objek Flask

# Validate Input
def validate_input(data):
    required_fields = ['user_account_number', 'ip_address_public', 'app_version', 'device_id', 'device_model', 'os_version']
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    return True, None

# Generate Yodu Ref No and Secret Key
def generate_yodu_ref_no():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def generate_secret_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Get User Data
def get_data_user(account_number):
    user_data = {
        "account_number": account_number,
        "name": "John Doe"
    }
    return user_data


# Encode Tags
def calculate_length(value):
    """Menghitung panjang dari value dalam format hexadecimal"""
    if isinstance(value, dict):
        # Jika value adalah dictionary, hitung panjang semua nested tags
        nested_length = 0
        for inner_tag, inner_value in value.items():
            nested_length += calculate_length(inner_value)  # Rekursif untuk tag bertingkat
        return nested_length
    elif isinstance(value, str):
        # Jika value adalah string, panjangnya adalah jumlah karakter (bytes)
        return len(value)  # Panjang dalam byte (1 karakter = 1 byte)
def encode_tag(tag, value):
    # Format pengekodan tag, ini akan disesuaikan dengan standar pengkodean yang Anda inginkan.
    
    if isinstance(value, dict):
        nested_tags = ''.join(encode_tag(inner_tag, inner_value) for inner_tag, inner_value in value.items())
        length_hex = f"{len(nested_tags) // 2:02X}"  # Menghitung panjang dalam byte
        return f"{tag}{length_hex}{nested_tags}"
    else:
        # Asumsi value adalah string
        hex_value = ''.join([f"{ord(c):02X}" for c in value])  # Convert string ke hex
        return f"{tag}{len(hex_value)//2:02X}{hex_value}"  # Menghitung panjang dalam byte dan mengonversinya

def parse_tlv(data):
    index = 0
    parsed_tags = []

    while index < len(data):
        # Ambil Tag
        if data[index:index + 2].startswith('5F') or data[index:index + 2].startswith('9F'):
            tag = data[index:index + 4]  # Tag dengan panjang 2 byte (contoh: 5F20, 9F25)
            index += 4
        else:
            tag = data[index:index + 2]  # Tag dengan panjang 1 byte (contoh: 85, 50)
            index += 2

        # Ambil Length
        length = int(data[index:index + 2], 16)  # Panjang dalam hex ke desimal
        index += 2

        # Ambil Value
        value = data[index:index + (length * 2)]  # Panjang value = length * 2 (karena hex)
        index += (length * 2)

        # Tambahkan ke array hasil
        parsed_tags.append({"Tag": tag, "Length": length, "Value": value})

    return parsed_tags


# Input Data
data = "8505435056303161A54F0E413030303030303630323230323050075152495343504D5A1E3132333435363738393039333630303931343330303534363637343838465F20084A6F686E20446F655F2D046964656E5F500B3139322E3136382E302E319F0805312E302E309F250437383930611B6465766963653132333B4D6F64656C583B416E64726F6964203131631E9F741B6368657175653A3332313334323936343437303536393231373636"

# Parsing
parsed_tags = parse_tlv(data)

# Cetak hasil
for tag in parsed_tags:
    print(f"Tag: {tag['Tag']}, Length: {tag['Length']}, Value: {tag['Value']}")


# Convert Hex to Base64
def hex_to_base64(hex_data):
    # Filter hanya karakter hexadecimal (0-9, A-F)
    valid_hex = ''.join(c for c in hex_data if c in '0123456789ABCDEFabcdef')
    try:
        hex_bytes = bytes.fromhex(valid_hex)
    except ValueError:
        return None  # Jika ada kesalahan dalam konversi, kembalikan None
    return base64.b64encode(hex_bytes).decode('utf-8')

def is_valid_hex(data):
    # Mengecek apakah data hanya berisi karakter hex (0-9, A-F)
    try:
        bytes.fromhex(data)
        return True
    except ValueError:
        return False

encoded_tags = '8543505630316107A0000006022020500751524390036534E696B6F204A6F616E746F6964656E69646D61696C746F3A6E696B6F40796F64752E6964332E312E329F2588886305352363563363531323766666339333433306435643031636433343533'

if is_valid_hex(encoded_tags):
    binary_data = bytes.fromhex(encoded_tags)
    print("Binary Data:", binary_data)
else:
    print("Invalid Hexadecimal Data")

def string_to_hex(input_string):
    """Convert a plain string to its hexadecimal representation."""
    return input_string.encode('utf-8').hex()

# Generate QR CPM
@app.route('/generate_qr_cpm', methods=['POST'])
def generate_qr_cpm():
    data = request.json

    is_valid, error_message = validate_input(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    yodu_ref_no = generate_yodu_ref_no()
    secret_key = generate_secret_key()
    validity_period = datetime.datetime.utcnow() + datetime.timedelta(minutes=2)
    timestamp = int(validity_period.timestamp())
    
    email_address = "mailto:niko@yodu.id "
    hex_value_5F50 = string_to_hex(email_address)
    
    user = "Niko Joanto "
    hex_value_5F20 = string_to_hex(user)
    
    app_version_number = "3.1.2"
    hex_value_9F08 = string_to_hex(app_version_number)
    
    
    
    issuer_qris_data = secret_key
    hex_value_9F74 = string_to_hex(issuer_qris_data)
    
    issuer_qris_data = secret_key
    hex_value_9F74 = string_to_hex(issuer_qris_data)
    
    tag_4F_value = "A0000006022020"
    hex_value_4F = tag_4F_value
    print(f"Hex Value for Tag 4F: {hex_value_4F}")
    print(f"Length of Tag 4F in bytes: {len(bytes.fromhex(hex_value_4F))}")  

    user_data = get_data_user(data['user_account_number'])

    # Flatten raw_tags dictionary and ensure all values are properly encoded
    def flatten_tags(tags):
        result = []
        for tag, value in tags.items():
            if isinstance(value, dict):
                result.extend(flatten_tags(value))  # Recursively flatten the nested dict
            else:
                result.append(encode_tag(tag, value))
        return result

    raw_tags = {
        "85": "CPV01",
        "61": {
            "4F": hex_value_4F,
            "50": "QRISCPM",
            "5A": "9360081271829304572F",
            "5F20": hex_value_5F20,
            "5F2D": "iden",
            "5F50": hex_value_5F50,
            "9F08": hex_value_9F08,
            "9F25": "9999",
            "63": {
                "9F74": hex_value_9F74
                
            }
        }
    }
    def print_tag_hex(tags):
        for tag, value in tags.items():
            if isinstance(value, dict):
                print_tag_hex(value)  # Recursively handle nested dictionaries
            else:
                print(f"Tag: {tag}, Hex Value: {value}")

    print_tag_hex(raw_tags)
    
    def print_tag_lengths(tags):
        for tag, value in tags.items():
            if isinstance(value, dict):
                print_tag_lengths(value)  # Recursively handle nested dictionaries
            else:
                print(f"Tag: {tag}, Length: {len(value)}")

    print_tag_lengths(raw_tags)

    # Flatten tags and encode
    encoded_tags = ''.join(flatten_tags(raw_tags))
    print(f"Encoded Tags: {encoded_tags}")

    print(f"5F50 Hex Value: {raw_tags['61']['5F50']}")
    print(f"5F20 Hex Value: {raw_tags['61']['5F20']}")
    # Ensure the encoded_tags string contains only valid hexadecimal characters
    encoded_tags = encoded_tags.replace(" ", "").upper()  # Remove spaces and ensure uppercase

    try:
        # Convert to binary
        binary_data = bytes.fromhex(encoded_tags)
        print(f"Binary Data: {binary_data}")
    except ValueError as e:
        print(f"Error converting to binary: {e}")
        return jsonify({"error": "Invalid hex encoding in tags"}), 400

    # Convert to base64
    base64_data = hex_to_base64(encoded_tags)

    return jsonify({
        "yodu_ref_no": yodu_ref_no,
        "secret_key": secret_key,
        "validity_period": validity_period.isoformat(),
        "base64_qr_cpm": base64_data,
        "timestamp": timestamp,
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
