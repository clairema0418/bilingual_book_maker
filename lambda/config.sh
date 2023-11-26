FUNCTION_NAME="bilingual_book_maker"


aws lambda get-function-configuration --function-name $FUNCTION_NAME

# aws lambda update-function-configuration --function-name $FUNCTION_NAME \
#    --kms-key-arn arn:aws:kms:us-east-2:123456789012:key/055efbb4-xmpl-4336-ba9c-538c7d31f599

aws lambda update-function-configuration --function-name $FUNCTION_NAME \
    --environment "Variables={BUCKET=my-bucket,KEY=file.txt}"