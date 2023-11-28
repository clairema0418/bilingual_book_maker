import sys
from pathlib import Path
from book_maker.utils import prompt_config_to_kwargs

from bs4 import BeautifulSoup  # Import BeautifulSoup for HTML parsing


class HTMLLoader:
    def __init__(
        self,
        html_path,
        model,
        key,
        resume,
        language,
        model_api_base=None,
        is_test=False,
        test_num=5,
        prompt_config=None,
        single_translate=False,
        context_flag=False,
        temperature=1.0,
    ) -> None:
        self.html_path = html_path  # Update to accept the HTML file path
        self.translate_model = model(
            key,
            language,
            api_base=model_api_base,
            temperature=temperature,
            **prompt_config_to_kwargs(prompt_config),
        )
        self.is_test = is_test
        self.p_to_save = []
        self.bilingual_result = []
        self.bilingual_temp_result = []
        self.test_num = test_num
        self.batch_size = 10
        self.single_translate = single_translate

        try:
            # Read and parse the HTML content
            with open(html_path, encoding="utf-8") as f:
                html_content = f.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                # Extract and store the text content from HTML
                self.origin_book = soup.get_text().splitlines()
        except Exception as e:
            raise Exception("can not load HTML file") from e

        self.resume = resume
        self.bin_path = f"{Path(html_path).parent}/.{Path(html_path).stem}.temp.bin"
        if self.resume:
            self.load_state()

    # Modify or add methods to handle HTML-specific processing as needed

    def make_bilingual_html(self):
        index = 0
        p_to_save_len = len(self.p_to_save)

        try:
            # Split HTML content into paragraphs or sections as needed
            # Modify the logic to handle HTML-specific structure
            # For example, you can use BeautifulSoup to extract paragraphs or sections
            # and then translate them
            # Here's a simplified example assuming paragraphs are enclosed in <p> tags:
            soup = BeautifulSoup("\n".join(self.origin_book), 'html.parser')
            paragraphs = soup.find_all('p')

            for paragraph in paragraphs:
                batch_text = paragraph.get_text()
                if self._is_special_text(batch_text):
                    continue
                if not self.resume or index >= p_to_save_len:
                    try:
                        temp = self.translate_model.translate(batch_text)
                    except Exception as e:
                        print(e)
                        raise Exception(
                            "Something is wrong when translate") from e
                    self.p_to_save.append(temp)
                    if not self.single_translate:
                        self.bilingual_result.append(batch_text)
                    self.bilingual_result.append(temp)
                index += 1
                if self.is_test and index > self.test_num:
                    break

            # Save the bilingual HTML content to a file
            self.save_html_file(
                f"{Path(self.html_path).parent}/{Path(self.html_path).stem}_bilingual.html",
                str(soup),
            )
        except (KeyboardInterrupt, Exception) as e:
            print(e)
            print("you can resume it next time")
            self._save_progress()
            self._save_temp_html()
            sys.exit(0)

    def _save_temp_html(self):
        index = 0
        sliced_list = [
            self.origin_book[i:i + self.batch_size]
            for i in range(0, len(self.origin_book), self.batch_size)
        ]

        for i in range(len(sliced_list)):
            batch_text = "\n".join(sliced_list[i])
            self.bilingual_temp_result.append(batch_text)
            if self._is_special_text(self.origin_book[i]):
                continue
            if index < len(self.p_to_save):
                self.bilingual_temp_result.append(self.p_to_save[index])
            index += 1

        # Save the temporary bilingual HTML content to a file
        self.save_html_file(
            f"{Path(self.html_path).parent}/{Path(self.html_path).stem}_bilingual_temp.html",
            "\n".join(self.bilingual_temp_result),
        )

    def save_temp_html_progress(self):
        try:
            with open(self.bin_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.p_to_save))
        except:
            raise Exception("can not save temporary HTML progress")

    def load_html_state(self):
        try:
            with open(self.bin_path, encoding="utf-8") as f:
                self.p_to_save = f.read().splitlines()
        except Exception as e:
            raise Exception("can not load HTML progress") from e

    def save_html_file(self, html_path, content):
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
        except:
            raise Exception("can not save HTML file")
