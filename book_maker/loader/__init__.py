from book_maker.loader.epub_loader import EPUBBookLoader
from book_maker.loader.txt_loader import TXTBookLoader
from book_maker.loader.srt_loader import SRTBookLoader
from book_maker.loader.html_loader import HTMLBookLoader
# from book_maker.loader.pdf_loader import PdfBookLoader
from book_maker.loader.docx_loader import DocxBookLoader
from book_maker.loader.csv_loader import CSVBookLoader

BOOK_LOADER_DICT = {
    "epub": EPUBBookLoader,
    "txt": TXTBookLoader,
    "srt": SRTBookLoader,
    "html": HTMLBookLoader,
    #   "pdf": PdfBookLoader,
    "docx": DocxBookLoader,
    "csv": CSVBookLoader,
    # TODO add more here
}
