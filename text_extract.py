
import fitz
import os
import glob

UPLOAD_FOLDER = "uploads"

pdf_files = glob.glob(os.path.join(UPLOAD_FOLDER, "*.pdf"))

if not pdf_files:
    print("No PDF found in uploads folder!")
else:
    pdf_path = pdf_files[-1]

    print("PDF found:", pdf_path)

    try:
        doc = fitz.open(pdf_path)
        print("Total pages:", len(doc))

        full_text = ""

        for page_number, page in enumerate(doc, start=1):
            text = page.get_text()
            full_text += text

            print(f"\n--- Page {page_number} ---")
            print(text[:1500] if text.strip()
                  else "No text found on this page.")

        print("\n--- RESULT ---")

        if full_text.strip():
            print("SUCCESS: PDF text extracted!")
            print("Total characters:", len(full_text))
        else:
            print("No selectable text found. PDF may be scanned.")

        doc.close()

    except Exception as e:
        print("ERROR:", e)
