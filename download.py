import gdown

file_id = "1bs1eFJbIVxc1Cxu9f0UAJheTlBaMNFT5"
url = f'https://drive.google.com/uc?id={file_id}'
output = 'luc_data.zip'
gdown.download(url, output, quiet=False)