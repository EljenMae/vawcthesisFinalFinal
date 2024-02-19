# Cryptography
from cryptography.fernet import Fernet

def encrypt_data(data):
    key = 'PkrcIv-ruqgLmgisRp3jkvohyOaTkrD2B_bE5-Upt_4='  # Replace with your encryption key
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data):
    key = 'PkrcIv-ruqgLmgisRp3jkvohyOaTkrD2B_bE5-Upt_4='  # Replace with your encryption key
    cipher_suite = Fernet(key.encode())
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
    return decrypted_data


# test = "b'gAAAAABl0O9SmggDWfdYVFwLAS1iPjWkjKxafT8WLn_YcYmyFdjsuAB8XBO5dFWEAqo6ktcwJw1FukqVOJpb_S78qg4DoA2xFQ=='"

# tese = test.split("'")[1]
# print(tese)


print(decrypt_data('gAAAAABl0y3epzAJH7tlB2pyPf9Me1iHPTK23y4ghUUi_71gh97nBJDSi2er37suhKRtkaJauRc9MvbOUZ_-3yMhpB0IkEoEyg=='))