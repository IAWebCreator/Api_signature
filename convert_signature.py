import base64
import os

def convert_image_to_base64(image_path):
    # Get the absolute path of the image
    abs_path = os.path.abspath(image_path)
    
    # Check if file exists
    if not os.path.exists(abs_path):
        print(f"Error: File not found at {abs_path}")
        print("Please make sure your signature file exists and enter the correct path.")
        return None
        
    with open(abs_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Ask for the signature file path
file_path = input("Enter the path to your signature file (e.g., C:\\Users\\YourUser\\Desktop\\@Firma.jpg): ")

# Convert your signature
signature_base64 = convert_image_to_base64(file_path)
if signature_base64:
    print("\nYour base64 signature (copy this to your .env file):\n")
    print(f"SIGNATURE_BASE64={signature_base64}") 