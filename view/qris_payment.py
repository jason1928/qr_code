import qrcode
import logging

class QRISPayment:
    
    def process(self, params):
        response = helper.response_msg(
            "QRIS_PAYMENT_SUCCESS",
            "QRIS PAYMENT SUCCESS",
            {}, "0000"
        )
        db_handle = database.get_database(config.payment_qrisDB)
        with db_handle.start_session() as lock:
            lock.start_transaction()
            try:
                fk_wallet_id = params.get("fk_wallet_id")
                fk_user_id = params.get("fk_user_id")
                qr_code = params.get("qr_code")
                wms_pin = params.get("pin")
                total_amount = float(params['total_amount'])
                total_tips_amount = params.get('total_tips_amount', 0)
                trx_id = None
                voucher_code = params.get("voucher_code", "")
                call_id = response.get("id")
                self.global_call_id = call_id

                use_voucher = False
                cashback_amount = 0
                disc_amount = 0
                final_amount = total_amount

                if total_tips_amount == "":
                    total_tips_amount = 0

                api_log_pkey = logging.insert_api_log({
                    "call_id": call_id,
                    "fk_wallet_id": fk_wallet_id,
                    "api_name": "/v1/api/qris/payment",
                    "req_host": "0.0.0.0:58002",
                    "req_route": "",
                    "req_data": params
                })

                # Generate QRIS Payment Code
                qr_data = self.generate_qris_data(fk_wallet_id, final_amount, trx_id, voucher_code)
                qr_code_img = self.generate_qr_code(qr_data)

                # Return response with QR Code image
                response["qr_code_image"] = qr_code_img
                return response

            except Exception as e:
                logging.error(f"Error processing QRIS payment: {str(e)}")
                response = helper.response_msg("QRIS_PAYMENT_ERROR", "Error processing QRIS payment", {}, "0001")
                return response

    def generate_qris_data(self, fk_wallet_id, amount, trx_id, voucher_code):
        """
        Function to create QRIS data string
        :param fk_wallet_id: Wallet ID
        :param amount: Payment amount
        :param trx_id: Transaction ID (optional)
        :param voucher_code: Voucher code (optional)
        :return: QRIS formatted data
        """
        qris_data = f"00020101021129370016ID{fk_wallet_id}{amount}{trx_id or ''}{voucher_code or ''}"
        # You can add more fields as per the QRIS specification

        return qris_data

    def generate_qr_code(self, data):
        """
        Generate QR Code for given data
        :param data: The QR data to encode
        :return: QR Code image as a base64 string or image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Return the QR Code as an image
        img = qr.make_image(fill="black", back_color="white")
        return img
