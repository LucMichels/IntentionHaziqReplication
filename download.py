import gdown

file_id = "1Md2sI8gG6EFj__d4qoGb3S0_vTJ5MvkU"
url = f'https://drive.google.com/uc?id={file_id}'
output = 'luc_data.zip'
gdown.download(url, output, quiet=False)