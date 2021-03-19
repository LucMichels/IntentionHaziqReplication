import gdown

file_id = "1hVv07o7EabJUQS67UYSHzq0ro_OBFc-5"
url = f'https://drive.google.com/uc?id={file_id}'
output = 'luc_data.zip'
gdown.download(url, output, quiet=False)