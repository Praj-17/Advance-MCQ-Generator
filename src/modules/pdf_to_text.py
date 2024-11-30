import fitz  # PyMuPDF

class PDFtoText:
    def __init__(self):
        pass

    def open_pdf(self, pdf):
        """
        Opens a PDF file from a file-like object or bytes.

        Args:
            pdf: The PDF file to open. Can be bytes or a file-like object.

        Returns:
            pdf_doc: The opened PDF document.
        """
        if not pdf:
            raise ValueError("PDF file is None or empty")

        if isinstance(pdf, bytes):
            pdf_doc = fitz.open(stream=pdf, filetype='pdf')
        elif hasattr(pdf, 'read'):
            pdf.seek(0)  # Reset file pointer to the beginning
            pdf_bytes = pdf.read()
            pdf_doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        else:
            raise ValueError("Invalid PDF input. Must be bytes or a file-like object.")

        return pdf_doc

    def extract_all_text(self, pdf):
        """
        Extracts all text from the PDF.

        Args:
            pdf: The PDF file to extract text from (bytes or file-like object).

        Returns:
            all_text: The extracted text as a single string.
        """
        if not pdf:
            return None
        with self.open_pdf(pdf) as doc:
            all_text = ''
            # Iterate through all pages
            for page_number in range(doc.page_count):
                # Get the page
                page = doc[page_number]
                # Extract text from the page
                text = page.get_text()
                all_text += text
        return all_text

    def extract_all_text_page_wise(self, pdf):
        """
        Extracts text from the PDF page by page.

        Args:
            pdf: The PDF file to extract text from (bytes or file-like object).

        Returns:
            all_text: A dictionary with page numbers as keys and page text as values.
        """
        if not pdf:
            return None
        with self.open_pdf(pdf) as doc:
            all_text = {}
            # Iterate through all pages
            for page_number in range(doc.page_count):
                # Get the page
                page = doc[page_number]
                # Extract text from the page
                text = page.get_text()
                all_text[str(page_number + 1)] = text
        return all_text

    def extract_text_from_single_page(self, pdf, page_number):
        """
        Extracts text from a single page of the PDF.

        Args:
            pdf: The PDF file to extract text from.
            page_number: The page number to extract (1-based indexing).

        Returns:
            text: The extracted text from the specified page.
        """
        if not pdf:
            return None
        with self.open_pdf(pdf) as doc:
            if page_number - 1 >= doc.page_count:
                raise ValueError("Invalid page number")
            else:
                return doc[page_number - 1].get_text()

    def extract_text_from_interval(self, pdf, page_number, interval=1):
        """
        Extracts text from a range of pages around a specified page.

        Args:
            pdf: The PDF file to extract text from.
            page_number: The central page number (1-based indexing).
            interval: The number of pages before and after the central page to include.

        Returns:
            text: The extracted text from the specified range of pages.
        """
        if not pdf:
            return None
        with self.open_pdf(pdf) as doc:
            text = ""
            if page_number > doc.page_count:
                raise ValueError("Invalid page number")
            else:
                # Calculate the start and end pages (0-based indexing)
                start_page = max(0, page_number - interval - 1)
                end_page = min(doc.page_count - 1, page_number + interval - 1)

                for page_num in range(start_page, end_page + 1):
                    text += doc[page_num].get_text()
        return text

# Example usage:
if __name__ == "__main__":
    import json
    pdftotext = PDFtoText()
    # Replace 'your_pdf_file.pdf' with the path to your PDF file for testing
    with open('your_pdf_file.pdf', 'rb') as pdf_file:
        text = pdftotext.extract_all_text_page_wise(pdf_file)
        with open("extracted_data.json", "w", encoding='utf-8') as f:
            json.dump(text, f, indent=4, ensure_ascii=False)
