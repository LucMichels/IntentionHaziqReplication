import gdown

file_id = "1xRmRoeRfAzqn3v5bTEnsopEZgpdSJHV0"
url = f'https://drive.google.com/uc?id={file_id}'
output = 'luc_data.zip'
gdown.download(url, output, quiet=False)