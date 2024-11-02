from flask import Flask, request, send_file, jsonify
import fitz  # PyMuPDF
import io
import os
import base64
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

def get_signature_from_env():
    """Get signature from environment variable and decode it with validation"""
    signature_base64 = os.getenv('SIGNATURE_BASE64')
    if not signature_base64:
        raise ValueError("Signature environment variable not found")
    
    try:
        # Decode base64 signature to bytes
        signature_bytes = base64.b64decode(signature_base64)
        
        # Validate that we have actual data
        if len(signature_bytes) == 0:
            raise ValueError("Empty signature data")
            
        # Open the image as a document
        img_doc = fitz.open(stream=signature_bytes, filetype="jpeg")  # Use "jpeg" if your image is in JPEG format
        
        # Load the first (and only) page
        img_page = img_doc.load_page(0)
        
        # Extract the pixmap (image)
        signature_image = img_page.get_pixmap()
        
        return signature_image
        
    except Exception as e:
        raise ValueError(f"Invalid signature data: {str(e)}")

@app.route('/add_signature', methods=['POST'])
def add_signature():
    if 'pdf' not in request.files:
        return jsonify({"error": "Please provide a PDF file with the key 'pdf'."}), 400

    pdf_file = request.files['pdf']

    try:
        # Get signature image from environment variable
        signature_image = get_signature_from_env()

        # Validate signature image dimensions
        if signature_image.width <= 0 or signature_image.height <= 0:
            return jsonify({"error": "Invalid signature image dimensions"}), 400

        # Load the PDF
        pdf_bytes = pdf_file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Find the last occurrence of "CONTRATISTA"
        last_coord = None
        last_page = None

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text_instances = page.search_for("CONTRATISTA")
            if text_instances:
                last_coord = text_instances[-1]
                last_page = page_num

        if last_coord is None:
            return jsonify({"error": "'CONTRATISTA' not found in the PDF."}), 404

        # Define the position and size
        insert_position = fitz.Point(last_coord.x0, last_coord.y1 + 10)
        
        # Define the size of the signature
        sig_width = signature_image.width
        sig_height = signature_image.height

        # Validate that the insertion point is within page bounds
        page = pdf_document[last_page]
        page_rect = page.rect
        
        if (insert_position.x + sig_width > page_rect.width or 
            insert_position.y + sig_height > page_rect.height):
            return jsonify({"error": "Signature position would be outside page bounds"}), 400

        # Insert the signature image
        page.insert_image(
            fitz.Rect(
                insert_position.x, 
                insert_position.y, 
                insert_position.x + sig_width, 
                insert_position.y + sig_height
            ),
            pixmap=signature_image,
            keep_proportion=True
        )

        # Save the modified PDF to a bytes buffer
        output_buffer = io.BytesIO()
        pdf_document.save(output_buffer)
        output_buffer.seek(0)

        # Clean up resources
        signature_image = None
        pdf_document.close()

        return send_file(
            output_buffer,
            as_attachment=True,
            download_name='signed_document.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": f"General error: {str(e)}"}), 500

@app.route('/test_signature', methods=['GET'])
def test_signature():
    try:
        signature_image = get_signature_from_env()
        
        return jsonify({
            "status": "success",
            "signature_info": {
                "width": signature_image.width,
                "height": signature_image.height,
                "size_bytes": len(signature_image.get_image())
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 