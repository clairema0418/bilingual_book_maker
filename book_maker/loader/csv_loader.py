import sys
import csv
from pathlib import Path

from book_maker.utils import prompt_config_to_kwargs

from .base_loader import BaseBookLoader
import boto3
import logging
import io
s3 = boto3.client('s3')


class CSVBookLoader(BaseBookLoader):
    def __init__(
        self,
        csv_name,
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
        bucket=None,
        upload_to_s3=False,
        language_key=None,

    ) -> None:
        self.csv_name = csv_name
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
        self.bucket = bucket
        self.upload_to_s3 = upload_to_s3
        self.language = language
        self.language_key = language_key

        try:
            self.origin_book = self.load_csv(csv_name)

        except Exception as e:
            raise Exception("can not load file") from e

        self.resume = resume
        self.bin_path = f"{Path(csv_name).parent}/.{Path(csv_name).stem}.temp.bin"
        if self.resume:
            self.load_state()

    @staticmethod
    def load_csv(csv_name):
        try:
            with open(csv_name, encoding="utf-8", newline='') as f:
                reader = csv.reader(f)
                lines = [row for row in reader]
                return lines
        except Exception as e:
            raise Exception("can not load CSV file") from e

    def _is_special_text(self, text):
        return text.isdigit() or text.isspace() or len(text) == 0

    def _make_new_book(self, book):
        pass

    def make_bilingual_book(self):
        index = 0
        p_to_save_len = len(self.p_to_save)

        try:
            for row in self.origin_book:
                bilingual_row = []
                for column in row:
                    if self._is_special_text(column):
                        bilingual_row.append(column)
                        continue
                    try:
                        temp = self.translate_model.translate(column)
                    except Exception as e:
                        print(e)
                        raise Exception(
                            "Something is wrong when translating") from e
                    bilingual_row.append(column)
                    bilingual_row.append(temp)
                    self.p_to_save.append(temp)
                self.bilingual_result.append(bilingual_row)
                index += 1
                if self.is_test and index >= self.test_num:
                    break

            self.save_file(
                f"{Path(self.csv_name).stem}_bilingual.csv",
                self.bilingual_result,
            )

        except (KeyboardInterrupt, Exception) as e:
            print(e)
            print("You can resume it next time")
            self._save_progress()
            self._save_temp_book()
            sys.exit(0)

    def _save_temp_book(self):
        index = 0
        bilingual_temp_result = []

        for row in self.origin_book:
            bilingual_row = []
            for column in row:
                bilingual_row.append(column)
                if not self._is_special_text(column) and index < len(self.p_to_save):
                    bilingual_row.append(self.p_to_save[index])
                    index += 1
            bilingual_temp_result.append(bilingual_row)

        self.save_file(
            f"{Path(self.csv_name).parent}/{Path(self.csv_name).stem}_bilingual_temp.csv",
            bilingual_temp_result,
        )

    def _save_progress(self):
        try:
            with open(self.bin_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.p_to_save))
        except:
            raise Exception("Can not save resume file")

    def load_state(self):
        try:
            with open(self.bin_path, encoding="utf-8") as f:
                self.p_to_save = f.read().splitlines()
        except Exception as e:
            raise Exception("Can not load resume file") from e

    def save_file(self, csv_path, content):
        logger = logging.getLogger()

        if self.upload_to_s3:
            try:
                # Create a BytesIO object to hold the content
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerows(content)

                logger.info(f"start write file: {csv_path}")
                upload_path = '{}/{}.csv'.format(self.language_key,
                                                 Path(self.csv_name).stem)
                csv_bytes = csv_buffer.getvalue()
                # logger.info("bytes : {}".format(csv_bytes))
                s3.put_object(Body=csv_bytes.encode('utf-8'),
                              Bucket=self.bucket, Key=upload_path)
                logger.info(f"upload file to s3: {upload_path}")

                logger.info(f"delete file: {csv_path}")
            except (Exception) as e:
                logging.error(e)
        else:
            try:
                with open(csv_path, "w", encoding="utf-8-sig", newline='') as f:
                    writer = csv.writer(f)
                    for row in content:
                        writer.writerow(row)
            except (Exception) as e:
                logging.error(e)
