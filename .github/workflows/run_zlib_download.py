# -*- coding: utf-8 -*-
import os
import zipfile

import requests

# assuming this script is run from the /controller directory
controller_folder_path = os.path.join("src", "controller")
zlib_folder_path = os.path.join(controller_folder_path, "zlib")

r = requests.get("https://www.zlib.net/zlib1213.zip", allow_redirects=True)
with open(zlib_folder_path + ".zip", "wb") as zlib_zip:
    zlib_zip.write(r.content)

with zipfile.ZipFile(zlib_folder_path + ".zip", "r") as zip_ref:
    zip_ref.extractall(controller_folder_path)

os.rename(f"{zlib_folder_path}-1.2.13", zlib_folder_path)
