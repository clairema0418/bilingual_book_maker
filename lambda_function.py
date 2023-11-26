
import argparse
from book_maker.cli import translate


def handler(event, context):
    options = argparse.Namespace(
        book_name=event['book_name'],
        language=event['language'],
        openai_key=event['openai_key'],
        api_base=event['api_base'],
        deployment_id=event['deployment_id'],
        folder_path=event['folder_path'],
        prompt=event['prompt'],
    )

    translate(options)
    return {
        'book_name': event['book_name'],
        'language': event['language'],
        'openai_key': event['openai_key'],
        'api_base': event['api_base'],
        'deployment_id': event['deployment_id'],
        'folder_path': event['folder_path'],
        'prompt': event['prompt'],
    }
