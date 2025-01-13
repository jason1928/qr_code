from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import base64
import qrcode
from io import BytesIO

app = Flask(__name__)

# Simulasi database akun
accounts = {
    "123456789": {
        "status": "active",
        "type": "regular",
        "balance": 100000,  # Dalam rupiah
        "transaction_limit": 50000,
    },
    "67890": {
        "status": "inactive",
        "type": "premium",
        "balance": 0,
        "transaction_limit": 100000,
    }
}

# Data QRIS default
qris_data_default = {
    'ADF_Name': "A0000006022020",
    'Application_Label': "QRISCPM",
    'PAN': "936012341123456789",
    'Template': "PM PT net Bumi Nantara ONLY",
    'Version': "01.00",
    'Cardholder_Name': "John Doe",
    'Issuer_URL': "https://www.bank.com",
    'Last_4_Digits_PAN': "6789",
    'Language_Preference': "ID",
    'Track_2_Equivalent': "1234567890ABCDE",
    'Token_Requestor_ID_Value': "ABC12345678",
    'Payload_Format_Indicator': "CPV01",
    'Payment_Account_Reference_Value': "98765432109876543210",
    'Application_Cryptogram': "12345678",
    'Template_Data': "PM PT net Bumi Nantara ONLY"
}

# Helper: Validasi akun
def validate_account(account_id):
    account = accounts.get(account_id)
    if not account:
        return False, "Account not found"
    if account["status"] != "active":
        return False, "Account is inactive"
    if account["balance"] <= 0:
        return False, "Account balance is insufficient"
    return True, account

# Helper: Hitung check digit menggunakan algoritma Luhn
def luhn_check_digit(pan):
    total = 0
    reverse_digits = pan[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)

# Helper: Validasi data QRIS CPM
def validate_qris_data(data):
    required_fields = [
        'ADF_Name', 'Application_Label', 'PAN', 'Template', 'Version',
        'Cardholder_Name', 'Issuer_URL', 'Last_4_Digits_PAN', 'Language_Preference',
        'Track_2_Equivalent', 'Token_Requestor_ID_Value', 'Payload_Format_Indicator',
        'Payment_Account_Reference_Value', 'Application_Cryptogram', 'Template_Data'
    ]
    for field in required_fields:
        if field not in data:
            raise KeyError(f"Missing field: {field}")
    return data

# Helper: Generate QRIS CPM berbasis Base64
def generate_qris_cpm_base64(account_id):
    check_digit = luhn_check_digit(account_id)
    qr_data = f"""
    000201010211
    29{account_id}{check_digit}YODUAPP
    5303360
    5802ID
    540510000.00
    5905User
    6015Jakarta
    6304
    """.strip()

    # Buat QR code
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Konversi ke Base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_base64

# Helper: Generate QR Code dari data QRIS CPM
def generate_qris_cpm(data):
    data = validate_qris_data(data)
    qris_string = (
        f"4F{data['ADF_Name']}"
        f"50{data['Application_Label']}"
        f"5A{data['PAN']}"
        f"63{data['Template']}"
        f"61{data['Version']}"
        f"5F20{data['Cardholder_Name']}"
        f"5F50{data['Issuer_URL']}"
        f"9F25{data['Last_4_Digits_PAN']}"
        f"5F2D{data['Language_Preference']}"
        f"57{data['Track_2_Equivalent']}"
        f"9F19{data['Token_Requestor_ID_Value']}"
        f"85{data['Payload_Format_Indicator']}"
        f"9F24{data['Payment_Account_Reference_Value']}"
        f"9F26{data['Application_Cryptogram']}"
        f"61{data['Template_Data']}"
    )

    # Generate QR code
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4
    )
    qr.add_data(qris_string)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Konversi QR Code ke base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return qr_base64

@app.route('/generate-qris', methods=['POST'])
def generate_qris():
    try:
        data = request.json
        if not data or 'account_id' not in data:
            return jsonify({"status": "error", "message": "Account ID is required"}), 400

        account_id = data['account_id']

        # Validasi akun
        is_valid, account_or_error = validate_account(account_id)
        if not is_valid:
            return jsonify({"status": "error", "message": account_or_error}), 400

        # Generate QRIS CPM
        qr_base64 = generate_qris_cpm_base64(account_id)

        # Set validity period to 2 minutes from now
        validity_period = (datetime.now() + timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')

        # Calculate countdown in seconds
        time_countdown = int((datetime.strptime(validity_period, '%Y-%m-%d %H:%M:%S') - datetime.now()).total_seconds())

        return jsonify({
            "status": "success",
            "qr_code_base64": qr_base64,
            "validity_period": validity_period,
            "time_countdown": time_countdown  # Include countdown in the response
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
