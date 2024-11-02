from flask import Flask, request, send_file, jsonify
import fitz  # PyMuPDF
import io
import os
import base64
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

def get_signature_from_env():
    """Get signature from environment variable and decode it"""
    signature_base64 = os.getenv('SIGNATURE_BASE64')
    if not signature_base64:
        raise ValueError("Signature environment variable not found")
    
    # Decode base64 signature to bytes
    signature_bytes = base64.b64decode(signature_base64)
    
    # Create a temporary buffer for the signature
    signature_buffer = io.BytesIO(signature_bytes)
    return signature_buffer

@app.route('/add_signature', methods=['POST'])
def add_signature():
    if 'pdf' not in request.files:
        return jsonify({"error": "Please provide a PDF file."}), 400

    pdf_file = request.files['pdf']

    try:
        # Get signature from environment variable
        signature_buffer = get_signature_from_env()

        # Load the PDF
        pdf_bytes = pdf_file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Load the signature image from buffer
        signature_image = fitz.Pixmap(fitz.csRGB, signature_buffer.getvalue())

        last_coord = None
        last_page = None

        # Iterate through pages to find the last occurrence of "CONTRATISTA"
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text_instances = page.search_for("CONTRATISTA")
            if text_instances:
                last_coord = text_instances[-1]
                last_page = page_num

        if last_coord is None:
            return jsonify({"error": "'CONTRATISTA' not found in the PDF."}), 404

        # Define the position below the found text
        insert_position = fitz.Point(last_coord.x0, last_coord.y1 + 20)  # 20 units below

        # Define the size of the signature
        sig_width = 100  # Adjust as needed
        sig_height = 50  # Adjust as needed

        # Insert the signature image
        pdf_document[last_page].insert_image(
            fitz.Rect(insert_position.x, insert_position.y, insert_position.x + sig_width, insert_position.y + sig_height),
            pixmap=signature_image,
            keep_proportion=True
        )

        # Save the modified PDF to a bytes buffer
        output_buffer = io.BytesIO()
        pdf_document.save(output_buffer)
        output_buffer.seek(0)

        return send_file(
            output_buffer,
            as_attachment=True,
            download_name='signed_document.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 