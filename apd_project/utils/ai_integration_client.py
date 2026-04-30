import requests
import os
import json
import mimetypes


class K3IntegrationClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.url = f"{base_url}/api/v1/violations"

    def send_violation(self, violation_types, confidence, image_path, area="Area A", camera="Kamera 1"):
        if isinstance(violation_types, str):
            violation_types = [violation_types]

        if not os.path.exists(image_path):
            print(f"❌ File tidak ditemukan: {image_path}")
            return None

        payload = {
            'violations' : json.dumps(violation_types),
            'confidence' : str(confidence),
            'area'       : area,
            'camera'     : camera,
        }

        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = 'image/jpeg'

        try:
            with open(image_path, 'rb') as img_file:
                files = {
                    'image': (os.path.basename(image_path), img_file, mime_type)
                }
                response = requests.post(
                    self.url,
                    data=payload,
                    files=files,
                    timeout=10
                )

            if response.status_code in [200, 201]:
                data = response.json()
                print(f"✅ Berhasil: {violation_types} | ID: {data.get('id', '?')}")
                return data
            else:
                print(f"⚠️ Gagal: {response.status_code} | {response.text}")
                return None

        except requests.exceptions.ConnectionError:
            print("❌ Backend tidak terjangkau.")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None