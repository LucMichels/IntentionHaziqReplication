import gdown

file_id = "1UQj3q77GYiMfeHBJ-kwP26-RKMhU1QOH"
url = f'https://drive.google.com/uc?id={file_id}'
output = 'luc_data.zip'
gdown.download(url, output, quiet=False)