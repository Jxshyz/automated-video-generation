import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdfs_into_slides(input_dir="./data", output_dir="./data/slides"):
    """
    Split two PDF presentations into individual slides and save them in a 'slides' folder.
    Dynamically handles varying slide counts.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define the input PDF files (adjusting for possible .pdf extension)
    possible_extensions = ["", ".pdf"]  # Try both with and without .pdf
    pdf_files = []
    for base_name in ["Presentation1", "Presentation2"]:
        found = False
        for ext in possible_extensions:
            file_path = os.path.join(input_dir, base_name + ext)
            if os.path.exists(file_path):
                pdf_files.append(file_path)
                found = True
                break
        if not found:
            print(f"Error: {base_name} (or {base_name}.pdf) not found in {input_dir}.")
            return

    # Process each PDF
    slide_counter = 1  # To number slides sequentially across both presentations
    total_slides = 0

    for pdf_file in pdf_files:
        try:
            # Read the PDF
            pdf_reader = PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)

            # Log the number of pages for clarity
            print(f"[+] {os.path.basename(pdf_file)} has {num_pages} slides.")

            # Split each page into a separate PDF
            for page_num in range(num_pages):
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])

                # Define output file path (e.g., slide_1.pdf, slide_2.pdf, ...)
                output_file = os.path.join(output_dir, f"slide_{slide_counter}.pdf")
                with open(output_file, "wb") as output_pdf:
                    pdf_writer.write(output_pdf)
                print(f"[+] Saved slide {slide_counter} to {output_file}")
                slide_counter += 1

            total_slides += num_pages

        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
            return

    # Verify total slide count
    print(f"\n[+] Total slides processed: {total_slides}")
    if total_slides not in [20, 22]:  # 14 + 6 = 20, 14 + 8 = 22
        print(f"Warning: Expected total slides to be 20 or 22, but got {total_slides}.")

if __name__ == "__main__":
    # Split the PDFs into individual slides
    split_pdfs_into_slides()

    print("\n[+] PDFs have been split into individual slides in ./data/slides.")
    print("You can now use these slides for further processing or video editing.")