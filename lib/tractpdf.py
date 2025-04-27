from PyPDF2 import PdfReader, PdfWriter
import os

def split_pdf_pages(input_pdf_path, output_folder):
    # 確保輸出資料夾存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 讀取 PDF
    reader = PdfReader(input_pdf_path)
    input_pdf_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        
        output_path = os.path.join(output_folder, f"{input_pdf_name}_{i+1}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        
        print(f"Saved: {output_path}")
    return [os.path.join(output_folder, f"{input_pdf_name}_{i+1}.pdf") for i in range(len(reader.pages))]