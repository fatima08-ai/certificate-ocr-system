import requests

url = "http://127.0.0.1:8000/extract-batch"

files = [
    ("files", open("sample_certificates/test.pdf", "rb")),
    ("files", open("sample_certificates/test.png", "rb")),
]

response = requests.post(url, files=files)
print(response.status_code)
print(response.json())