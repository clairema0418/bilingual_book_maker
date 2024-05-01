import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from bs4 import BeautifulSoup
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from book_maker.utils import prompt_config_to_kwargs
from decimal import Decimal
from .base_loader import BaseBookLoader
import pdfplumber
import logging
import boto3
import io
from docx import Document
from fpdf import FPDF
s3 = boto3.client('s3')


class PdfBookLoader(BaseBookLoader):
    def __init__(
        self,
        pdf_name,
        model,
        key,
        resume,
        language,
        model_api_base=None,
        is_test=False,
        test_num=5,
        prompt_config=None,
        temperature=1.0,
        single_translate=True,
        context_flag=False,
        bucket=None,
        upload_to_s3=False,
        language_key=None,
    ) -> None:
        self.pdf_name = pdf_name
        self.translate_model = model(
            key,
            language,
            api_base=model_api_base,
            temperature=float(temperature),  # Convert temperature to Decimal
            **prompt_config_to_kwargs(prompt_config),
        )
        self.is_test = is_test
        self.p_to_save = []
        self.bilingual_result = []
        self.bilingual_temp_result = []
        self.test_num = test_num
        self.batch_size = 10
        self.bucket = bucket
        self.single_translate = True
        self.upload_to_s3 = False  # upload_to_s3
        self.language_key = language_key

        print(pdf_name)
        try:
            with open(pdf_name, "rb") as f:
                pdf = PdfReader(f)
                self.origin_book = ""
                for page in range(len(pdf.pages)):
                    self.origin_book += pdf.pages[page].extract_text() + "\n"

        except Exception as e:
            raise Exception("can not load file") from e

        self.resume = resume
        self.bin_path = f"{Path(pdf_name).parent}/.{Path(pdf_name).stem}.temp.bin"
        if self.resume:
            self.load_state()

    @staticmethod
    def _is_special_text(text):
        return text.isdigit() or text.isspace() or len(text) == 0

    def _make_new_book(self):
        pass

    def make_bilingual_book(self):
        index = 0
        p_to_save_len = len(self.p_to_save)
        logger = logging.getLogger()

        doc = Document()  # Create a new Word document
        try:
            pdf = PdfReader(open(self.pdf_name, 'rb'))
            pdf_writer = PdfWriter()

            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                # Extract text content and positions using pdfplumber
                pdfplumber_page = pdfplumber.open(
                    self.pdf_name).pages[page_num]
                text_elements = pdfplumber_page.extract_words()
                page_text = page.extract_text()

                if self._is_special_text(page_text):
                    continue

                if not self.resume or index >= p_to_save_len:
                    try:
                        logger.info(f"text: {page_text}")
                        translated_text = self.translate_model.translate(
                            page_text)
                    except Exception as e:
                        print(e)
                        raise Exception(
                            "Something is wrong when translating") from e

                    # Create a new page with the same size as the original page
                    # new_page = canvas.Canvas(io.BytesIO())
                    # new_page.setPageSize(
                    #     (page.mediabox.width, page.mediabox.height))

                    # # Draw the translated text on the new page
                    # # Adjust the coordinates as needed
                    # x_position = 100  # X-coordinate remains the same
                    # y_position = 700  # Initial Y-coordinate (adjust as needed)
                    # line_height = 12  # Adjust the line height as needed
                    # for line in translated_text:
                    #     # if line.strip():
                    #     # pdf.cell(0, 10, txt=line.encode(
                    #     #     'latin-1', 'replace').decode('latin-1'), ln=True)
                    #     new_page.drawString(x_position, y_position, line)
                    #     y_position -= line_height

                    # new_page.showPage()
                    # new_page.save()

                    # # Merge the new page into the output PDF
                    # new_page_pdf = PdfReader(
                    #     io.BytesIO(new_page.getpdfdata()))
                    # page.merge_page(new_page_pdf.pages[0])

                    self.p_to_save.append(translated_text)

                    if not self.single_translate:
                        self.bilingual_result.append(page_text)
                    self.bilingual_result.append(translated_text)

                # pdf_writer.add_page(page)
                index += 1

                if self.is_test and index > self.test_num:
                    break

            output_file = f"{Path(self.pdf_name).parent}/tmp/{Path(self.pdf_name).stem}_bilingual.pdf"
            # print("output_file", output_file)
            with open(output_file, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)
            self.save_file(
                output_file,
                self.bilingual_result,
            )

        except (KeyboardInterrupt, Exception) as e:
            print(e)
            print("you can resume it next time")
            self._save_progress()
            self._save_temp_book()
            sys.exit(0)

    def _save_temp_book(self):
        index = 0
        soup = BeautifulSoup(self.origin_book, 'html.parser')
        p_tags = soup.find_all('p')

        for p_tag in p_tags:
            batch_text = p_tag.get_text()
            self.bilingual_temp_result.append(batch_text)
            if self._is_special_text(batch_text):
                continue
            if index < len(self.p_to_save):
                self.bilingual_temp_result.append(self.p_to_save[index])
            index += 1

        upload_path = '{}/{}.pdf'.format(self.language_key,
                                         Path(self.pdf_name).stem)

        self.save_file(
            upload_path,
            str(soup),
        )

    def _save_progress(self):
        try:
            with open(self.bin_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.p_to_save))
        except:
            raise Exception("can not save resume file")

    def load_state(self):
        try:
            with open(self.bin_path, encoding="utf-8") as f:
                self.p_to_save = f.read().splitlines()
        except Exception as e:
            raise Exception("can not load resume file") from e

    def save_file(self, book_path, content):
        logger = logging.getLogger()
        if self.upload_to_s3:
            try:
                upload_path = '{}/{}.pdf'.format(
                    self.language_key, Path(self.pdf_name).stem)
                s3.put_object(Body=content, Bucket=self.bucket,
                              Key=upload_path)
                logger.info(f"upload file to S3: {upload_path}")
                os.remove(book_path)
                logger.info(f"delete file: {book_path}")
            except (Exception) as e:
                print("儲存檔案失敗")
                print(e)
        else:
            try:
                class PDF(FPDF):
                    def __init__(self):
                        super().__init__()
                        self.bilingual_result = []  # Add 'bilingual_result' attribute

                    def save_file(self, book_path, content):
                        try:
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            paragraphs = [content[i:i+100]
                                          for i in range(0, len(content), 100)]

                            for paragraph in paragraphs:
                                # if paragraph.strip():
                                print("寫入pdf段落:", paragraph)
                                pdf.cell(0, 10, txt=paragraph.encode(
                                    'latin-1', 'replace').decode('latin-1'), ln=True)
                                pdf.ln()
                            # Only write translated text, ignore empty lines
                            # for line in content:
                            #     # if line.strip():
                            #     print("寫入pdf:", line)
                            #     pdf.cell(0, 10, txt=line.encode(
                            #         'latin-1', 'replace').decode('latin-1'), ln=True)
                            #     pdf.ln()
                            print("pdf路徑:", book_path)
                            pdf.output(book_path, "F")  # Save as PDF
                        except Exception as e:
                            print("e", e)
                            raise Exception("Unable to save file") from e

                pdf = PDF()
                # Call the 'save_file' method of the PDF class
                print("pdf路徑2:", book_path)
                pdf.save_file(book_path, content)
                txt_book_path = f"{Path(self.pdf_name).parent}/tmp/{Path(self.pdf_name).stem}_bilingual.txt"
                with open(txt_book_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(content))
            except:
                raise Exception("can not save file")
