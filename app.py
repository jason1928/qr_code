from flask import Flask, request, jsonify
import base64
import uuid
import datetime

app = Flask(__name__)

def validate_input(data):
    required_fields = ['user_account_number', 'device_id', 'device_model', 'os_version', 'app_version', 'ip_address_public']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing or empty field: {field}"
    return True, None

def generate_yodu_ref_no():
    return str(uuid.uuid4())

def generate_secret_key():
    return base64.b64encode(uuid.uuid4().bytes).decode('utf-8')

def get_data_user(user_account_number):
    # Hardcoded user data for now
    return {
        "name": "Riki Derian",
        "account_number": user_account_number,
        "balance": 1000000
    }

def set_tag_data(user_data, additional_data):
    tags = {
        "85": "CPV01",
        "61": "A0000006022020",
        "4F": "A0000006022020",  # ADF Name
        "50": "QRISCPM",  # Application Label
        "5A": f"{user_data['account_number']}9360091430054667488F",  # Application PAN (up to 10 digits)
        "57": f"{user_data['account_number']}D221212345F",  # Track 2 Equivalent Data
        "5F20": user_data["name"],  # Cardholder's Name
        "5F2D": "iden",  # Language Preference
        "5F50": additional_data["ip_address_public"],  # Issuer URL
        "9F08": additional_data["app_version"],  # Application Version Number
        "9F25": user_data["account_number"][-4:],  # Last 4 Digits of PAN
        "9F19": "123456",  # Token Requestor ID (example)
        "9F24": "UNIQUEPAYMENTACCOUNTREF",  # Payment Account Reference
        "63": "9F743C" + "1234567890" * 5,  # Issuer Proprietary Data
        "9F36": "0010",  # Application Transaction Counter
        "82": "1234",  # Application Interchange Profile
        "9F37": "12345678",  # Unpredictable Number
        "9F39": "12345678",  # Terminal Verification Results        
    }
    # List of tags to exclude from hexadecimal conversion
    exclude_tags = ["5A", "4F", "9F25"]
    
    # Convert tags to hexadecimal, excluding specified tags
    converted_tags = convert_tags_to_hexadecimal(tags, exclude_tags)
    
    return converted_tags
def convert_tags_to_hexadecimal(tags, exclude_tags):
    """
    Converts each tag value to hexadecimal except for excluded tags.
    
    :param tags: Dictionary of tags and their values
    :param exclude_tags: List of tag keys to exclude from conversion
    :return: Updated tags dictionary with converted values
    """
    updated_tags = {}
    
    for tag, value in tags.items():
        if tag in exclude_tags:
            # Keep the original value for excluded tags
            updated_tags[tag] = value
        else:
            # Convert the value to hexadecimal
            updated_tags[tag] = value.encode("utf-8").hex()
    
    return updated_tags

def combine_tag_data(tags):
    combined_data = ""
    for tag, value in tags.items():
        length = len(value.encode('utf-8'))  # Calculate length in bytes
        combined_data += f"{tag}{length:02X}{value}"
    return combined_data

def trim_data(data):
    return data[:512] if len(data) > 512 else data

def to_hex(data):
    return data.encode("utf-8").hex()

def to_base64(data):
    return base64.b64encode(bytes.fromhex(data)).decode("utf-8")

@app.route('/generate_qr_cpm', methods=['POST'])
def generate_qr_cpm():
    data = request.json

     # Step 1: Validate Input
    is_valid, error_message = validate_input(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # Step 2: Generate Yodu Ref No
    yodu_ref_no = generate_yodu_ref_no()

    # Step 3: Generate Secret Key
    secret_key = generate_secret_key()

    # Step 4: Set Validity Period (2 minutes from now)
    validity_period = datetime.datetime.utcnow() + datetime.timedelta(minutes=2)

    # Step 5: Get User Data
    user_data = get_data_user(data['user_account_number'])

    # Step 6: Set Tag Data
    tags = set_tag_data(user_data, data)
    
    # Step 7: Convert Tags to Hexadecimal
    converted_tags = convert_tags_to_hexadecimal(tags, exclude_tags=["5A", "4F", "9F25"])

    # Step 8: Combine Tag Data
    combined_data = combine_tag_data(tags)

    # Step 9: Trim Data
    trimmed_data = trim_data(combined_data)

    # Step 10: Convert to Hex
    hex_data = to_hex(trimmed_data)  # HEX encoding
    print(f"HEX Data: {hex_data}")

    # Step 11: Convert HEX to Binary
    binary_data = bytes.fromhex(hex_data)  # Convert HEX to Binary
    print(f"Binary Data: {binary_data}")

    # Step 12: Convert Binary to Base64
    base64_data = base64.b64encode(binary_data).decode("utf-8")  # Convert Binary to Base64
    print(f"Base64 Data: {base64_data}")

    return jsonify({"base64_qr_cpm": base64_data}), 200

if __name__ == '__main__':
    app.run(debug=True)
