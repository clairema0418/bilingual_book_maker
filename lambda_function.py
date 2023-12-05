
import logging
import argparse
from book_maker.cli import translate
import boto3
import os
s3 = boto3.client('s3')


def handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    records = event.get('Records', [])

    for record in records:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        #  建立 Lambda /tmp 目錄下的文件路徑
        download_path = '/tmp/{}'.format(os.path.basename(key))
        # 將 S3 上的檔案下載到 Lambda /tmp 目錄下
        s3.download_file(bucket, key, download_path)
        logger.info(f"download_path: {download_path}")

        language = os.environ['language']
        options = argparse.Namespace(
            book_name=download_path,
            file_path=download_path,
            language=language,
            openai_key=os.environ['openai_key'],
            api_base=os.environ['api_base'],
            deployment_id=os.environ['deployment_id'],
            folder_path=os.environ['folder_path'],
            prompt=os.environ['prompt'],
            single_translate=os.environ['single_translate'],
        )

        # 開始進行翻譯
        translate(options)

        # 將檔案上傳到 S3
        upload_path = '{}/{}'.format(language, os.path.basename(key))
        s3.upload_file(download_path, bucket, upload_path)
        logger.info(f"upload file to s3: {upload_path}")

        # 刪除 Lambda /tmp 目錄下的檔案
        os.remove(download_path)
        logger.info(f"remove tmp file: {download_path}")

    return {
        'statusCode': 200,
        'body': 'Lambda function executed successfully.'
    }
