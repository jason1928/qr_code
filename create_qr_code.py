import qrcode

# Data yang akan dikodekan dalam QR Code
data = "https://contoh.com"

# Membuat QR Code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(data)
qr.make(fit=True)

# Membuat gambar QR Code
img = qr.make_image(fill_color="black", back_color="white")

# Menyimpan gambar QR Code
img.save("qrcode.png")

# Menampilkan gambar QR Code
img.show()
