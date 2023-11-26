FROM public.ecr.aws/lambda/python:3.11

# WORKDIR /app

COPY requirements.txt setup.py ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install --upgrade pip \
   && pip install --no-cache-dir -r requirements.txt

COPY . .
# # Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.handler" ]
# # ENTRYPOINT ["python3", "make_book.py"]

