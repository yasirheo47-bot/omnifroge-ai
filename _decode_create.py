import base64, json

# Decode the /app/create response body
body_b64 = 'eyJhZGRyZXNzIjoiYmVubWlsLmVzLjczMC4wQGdtYWlsLmNvbSIsInRpbWVzdGFtcCI6MTc3NzI4MzU4NCwia2V5IjoiZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SmtZWFJoSWpvaVltVnVibWxzTG1WekxqY3pNQzR3UUdkdFlXbHNMbU52YlNJc0ltTnlaV0YwWldSZllYUWlPakUzTnpjeU9ETTFPRFk5Lm5oSTFKdWlRUTBIeDkzazRVSG00UFdWY180c2lpREkySUEtOUo1dTlSN3MiLCJtZXNzYWdlcyI6W119'
decoded = base64.urlsafe_b64decode(body_b64 + '==').decode('utf-8', 'replace')
print('BODY:', decoded)
print()

d = json.loads(decoded)
key_jwt = d['key']
print('KEY JWT:', key_jwt)
parts = key_jwt.split('.')
payload = base64.urlsafe_b64decode(parts[1] + '==').decode()
print('KEY JWT PAYLOAD:', payload)
