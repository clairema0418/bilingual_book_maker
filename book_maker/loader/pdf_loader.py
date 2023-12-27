# import sys
# from pathlib import Path
# from PyPDF2 import PdfReader
# from bs4 import BeautifulSoup
# from fpdf import FPDF
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# from book_maker.utils import prompt_config_to_kwargs
# from decimal import Decimal
# from .base_loader import BaseBookLoader
# import pdfplumber


# class PdfBookLoader(BaseBookLoader):
#     def __init__(
#         self,
#         pdf_name,
#         model,
#         key,
#         resume,
#         language,
#         model_api_base=None,
#         is_test=False,
#         test_num=5,
#         prompt_config=None,
#         temperature=1.0,
#         single_translate=False,
#         context_flag=False,
#     ) -> None:
#         self.pdf_name = pdf_name
#         self.translate_model = model(
#             key,
#             language,
#             api_base=model_api_base,
#             temperature=float(temperature),  # Convert temperature to Decimal
#             **prompt_config_to_kwargs(prompt_config),
#         )
#         self.is_test = is_test
#         self.p_to_save = []
#         self.bilingual_result = []
#         self.bilingual_temp_result = []
#         self.test_num = test_num
#         self.batch_size = 10
#         self.single_translate = False

#         print(pdf_name)
#         try:
#             with open(pdf_name, "rb") as f:
#                 pdf = PdfReader(f)
#                 self.origin_book = ""
#                 for page in range(len(pdf.pages)):
#                     self.origin_book += pdf.pages[page].extract_text() + "\n"

#         except Exception as e:
#             raise Exception("can not load file") from e

#         self.resume = resume
#         self.bin_path = f"{Path(pdf_name).parent}/.{Path(pdf_name).stem}.temp.bin"
#         if self.resume:
#             self.load_state()

#     @staticmethod
#     def _is_special_text(text):
#         return text.isdigit() or text.isspace() or len(text) == 0

#     def _make_new_book(self):
#         pass

#     def make_bilingual_book(self):
#         index = 0
#         p_to_save_len = len(self.p_to_save)

#         try:
#             # 获取原始PDF的页面大小
#             with open(self.pdf_name, "rb") as f:
#                 pdf = PdfReader(f)
#                 first_page = pdf.pages[0]
#                 page_width = first_page.mediabox.width
#                 page_height = first_page.mediabox.height

#             # 创建一个新的PDF文档，使用与原始PDF相同的页面大小
#             output_pdf = canvas.Canvas(
#                 f"{Path(self.pdf_name).parent}/{Path(self.pdf_name).stem}_bilingual.pdf",
#                 pagesize=(page_width, page_height)
#             )

#             with open(self.pdf_name, "rb") as f:
#                 pdf = PdfReader(f)
#                 for page in range(len(pdf.pages)):
#                     page_text = pdf.pages[page].extract_text()
#                     words = pdfplumber.open(
#                         self.pdf_name).pages[page].extract_words()

#                     if self._is_special_text(page_text):
#                         # If the text is special characters, directly add it to the new PDF
#                         output_pdf.drawString(100, 700, page_text)
#                     else:
#                         try:
#                             # Translate the text
#                             translated_text = self.translate_model.translate(
#                                 page_text)
#                         except Exception as e:
#                             print(e)
#                             raise Exception(
#                                 "Error occurred during translation") from e

#                         # Replace the text at the correct position
#                         for word in words:
#                             if word["text"] == page_text:
#                                 x = word["x"]
#                                 y = word["y"]
#                                 output_pdf.drawString(x, y, translated_text)
#                                 break

#                     if self.is_test:
#                         break
#             # 保存新的PDF文件
#             output_pdf.showPage()
#             output_pdf.save()

#         except (KeyboardInterrupt, Exception) as e:
#             print(e)
#             print("you can resume it next time")
#             self._save_progress()
#             self._save_temp_book()
#             sys.exit(0)

#     def _save_temp_book(self):
#         index = 0
#         soup = BeautifulSoup(self.origin_book, 'html.parser')
#         p_tags = soup.find_all('p')

#         for p_tag in p_tags:
#             batch_text = p_tag.get_text()
#             self.bilingual_temp_result.append(batch_text)
#             if self._is_special_text(batch_text):
#                 continue
#             if index < len(self.p_to_save):
#                 self.bilingual_temp_result.append(self.p_to_save[index])
#             index += 1

#         self.save_file(
#             f"{Path(self.pdf_name).parent}/{Path(self.pdf_name).stem}_bilingual_temp.docx",
#             str(soup),
#         )

#     def _save_progress(self):
#         try:
#             with open(self.bin_path, "w", encoding="utf-8") as f:
#                 f.write("\n".join(self.p_to_save))
#         except:
#             raise Exception("can not save resume file")

#     def load_state(self):
#         try:
#             with open(self.bin_path, encoding="utf-8") as f:
#                 self.p_to_save = f.read().splitlines()
#         except Exception as e:
#             raise Exception("can not load resume file") from e

#     def save_file(self, book_path, content):
#         try:
#             class PDF(FPDF):
#                 def __init__(self):
#                     super().__init__()
#                     self.bilingual_result = []  # Add 'bilingual_result' attribute

#                 def save_file(self, book_path, content):
#                     try:
#                         pdf = FPDF()
#                         pdf.add_page()
#                         pdf.set_font("Arial", size=12)
#                         for line in content.split("\n"):
#                             # Use 'latin-1' encoding
#                             pdf.cell(0, 10, txt=line.encode(
#                                 'latin-1', 'replace').decode('latin-1'), ln=True)
#                         pdf.output(book_path, "F")  # Save as PDF
#                     except:
#                         raise Exception("can not save file")

#             pdf = PDF()
#             # Call the 'save_file' method of the PDF class
#             pdf.save_file(book_path, content)

#         except:
#             raise Exception("can not save file")
