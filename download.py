import gdown

file_id = "1W-YVkdBJU74xveTf97uo784gZIAw9aHe"
url = f'https://drive.google.com/uc?id={file_id}'
output = 'luc_data.zip'
gdown.download(url, output, quiet=False)