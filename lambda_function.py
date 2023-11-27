
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

        #  Lambda /tmp 目錄下的文件路徑
        download_path = '/tmp/{}'.format(os.path.basename(key))
        s3.download_file(bucket, key, download_path)
        logger.info(f"download_path: {download_path}")
        options = argparse.Namespace(
            file_path=download_path,
            language=os.environ['language'],
            openai_key=os.environ['openai_key'],
            api_base=os.environ['api_base'],
            deployment_id=os.environ['deployment_id'],
            folder_path=os.environ['folder_path'],
            prompt=os.environ['prompt'],
        )

        options.file_path = download_path

        # translate(options)

        os.remove(download_path)
        logger.info(f"remove file: {download_path}")

    return {
        'statusCode': 200,
        'body': 'Lambda function executed successfully.'
    }
