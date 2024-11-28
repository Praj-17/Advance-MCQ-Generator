# Get input PDF
from src import OpenAiRunnerClass, ChromaVectorStore, PDFtoText
import json

class AdvanceQuestionGenerator:
    def __init__(self) -> None:
        self.openai = OpenAiRunnerClass()
        self.RAG = ChromaVectorStore()
        self.pdf = PDFtoText()
    # Generate Level_1
    def generate_level_1(self, pdf_path):

        all_text = self.pdf.extract_all_text(pdf_path)
        # Read the entire PDF and pass it to one funcion
        res = self.openai.generate_topics_and_mcqs(context= all_text)

        return res
    def _process_input_pdf(self, pdf_path):
        pdf_name = pdf_path.split('/')[-1]

        pdf_name.replace(" ", "_").replace(".", "_")
        return pdf_name
    
    def _process_documents_context(rag_output):
        pass
    
    def generate_level_2(self, pdf_path):
        all_text_str = self.pdf.extract_all_text(pdf_path)
        all_text = self.pdf.extract_all_text_page_wise(pdf_path)
        collection_name = self._process_input_pdf(pdf_path)
        self.RAG.store_texts(all_text, collection_name=collection_name)

        # Now generate all relevant Topics
        book_info = self.openai.generate_book_title(all_text_str)
        for topic in book_info.get("main_topics"):
            results, output = self.RAG.fetch_relevant_documents(topic, collection_name)
        print(output)


    # Generate Level_2

if __name__ == "__main__":
    gen = AdvanceQuestionGenerator()
    res = gen.generate_level_1(r"data\Project Management.pdf")

    with open("level_1.json", "w") as f:
        json.dump(res, f, indent=4)




