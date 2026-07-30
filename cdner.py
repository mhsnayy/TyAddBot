import requests
import os

class TrendyolAssetUploader:
    def __init__(self, token: str):
        self.base_url = "https://apigw.trendyol.com/discovery-displayads-editorbff-service/upload/image"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def upload(self, file_path: str, platform: str = "stb-web") -> str:
        if not os.path.exists(file_path):
            return f"❌ [HATA] Dosya bulunamadı: {file_path}"
            
        ext = os.path.splitext(file_path)[1].lower()
        url = f"{self.base_url}/{platform}"
        
        # Trendyol'un form-data içinde bekleyebileceği olası anahtar kelimeler
        possible_form_keys = ['image', 'file', 'banner', 'upload', 'multipartFile', 'fileData']
        
        print(f"[{platform.upper()}] Yükleniyor... ({file_path})")
        
        for key in possible_form_keys:
            try:
                # Dosyayı her denemede yeniden okumalıyız
                with open(file_path, 'rb') as f:
                    # Dinamik anahtar kelime ataması
                    files = {key: (os.path.basename(file_path), f, f'image/{ext.replace(".", "")}')}
                    
                    response = requests.post(url, headers=self.headers, files=files, timeout=15)
                    
                    if response.status_code in [200, 201]:
                        cdn_url = response.json().get("absoluteUrl")
                        print(f"✅ Doğru anahtar kelime bulundu: '{key}'")
                        return f"✅ BAŞARILI: {cdn_url}"
                    elif response.status_code == 400 and "Unexpected field" in response.text:
                        # Yanlış anahtar kelime, sonrakini dene
                        print(f"  - '{key}' reddedildi, sonrakine geçiliyor...")
                        continue
                    else:
                        # Farklı bir hata varsa (Yetki, boyut vs.) döngüyü kır ve göster
                        return f"❌ BAŞARISIZ (HTTP {response.status_code}): {response.text}"

            except Exception as e:
                return f"❌ HATA: {e}"
                
        return "❌ [BAŞARISIZ] Olası tüm anahtar kelimeler (form-data keys) denendi ama Trendyol hiçbirini kabul etmedi. F12 Ağ (Network) sekmesinden kontrol etmemiz gerekiyor."

# --- Kullanım Senaryosu ---
if __name__ == "__main__":
    TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3ODU0MDExMDAsImV4cCI6MTc4NTQ4NzUwMCwiZW1haWwiOiJlcmJhdGFiQGdtYWlsLmNvbSIsInVzZXJJZCI6MjIwMSwicGVybWlzc2lvbnMiOlt7ImlkIjoxLCJuYW1lIjoiY2FuVmlld01QUmVwb3J0cyJ9LHsiaWQiOjQsIm5hbWUiOiJjYW5WaWV3QWNjb3VudERldGFpbCJ9LHsiaWQiOjc0LCJuYW1lIjoiY2FuVmlld1Byb2R1Y3RVcGRhdGUifSx7ImlkIjozNSwibmFtZSI6ImNhblZpZXdDb3Vwb24ifSx7ImlkIjo4MSwibmFtZSI6ImNhblZpZXdEaXNwbGF5QWRzIn0seyJpZCI6ODIsIm5hbWUiOiJjYW5WaWV3SW5mbHVlbmNlckFkcyJ9LHsiaWQiOjcyLCJuYW1lIjoiY2FuVmlld0FkcyJ9LHsiaWQiOjc2LCJuYW1lIjoiY2FuVmlld1Byb2R1Y3RBZHMifSx7ImlkIjo3NywibmFtZSI6ImNhblZpZXdCYW5uZXJBZHMifSx7ImlkIjo3OCwibmFtZSI6ImNhblZpZXdUdk91dGRvb3JBZHMifSx7ImlkIjoyLCJuYW1lIjoiY2FuVmlld0xpbmtzIn0seyJpZCI6NzMsIm5hbWUiOiJjYW5WaWV3RmluYW5jZSJ9LHsiaWQiOjgzLCJuYW1lIjoiY2FuVmlld1N0b3JlQWRzIn0seyJpZCI6MTI0LCJuYW1lIjoiY2FuVmlld1NlZ21lbnRzIn0seyJpZCI6ODAsIm5hbWUiOiJjYW5WaWV3TGlua1JlcG9ydHMifV0sImNvbnRhY3ROYW1lIjoiWmFmZXIiLCJjb250YWN0U3VybmFtZSI6IkF2aW5kaWsiLCJhY2NvdW50SWQiOjExNzMsImFjY291bnROYW1lIjoiRXJiYXRhYiIsImNhblZpZXdEaXN0cmlidXRvckJhc2VkUmVwb3J0IjpmYWxzZX0.M-IQjZYEGoAlKKJtrynDeUSF6Ei3rKNWHtX0ZuH_U_Y"
    
    uploader = TrendyolAssetUploader(token=TOKEN)
    
    # 1. WEB Görseli
    web_path = input("🖥️  WEB görselinin dosya yolu (Atlamak için boş bırakın): ").strip().strip('"').strip("'") 
    if web_path:
        web_result = uploader.upload(file_path=web_path, platform="stb-web")
        print(f"Sonuç:\n{web_result}\n")
        
    # 2. MOBİL Görseli
    mobile_path = input("📱 MOBİL görselinin dosya yolu (Atlamak için boş bırakın): ").strip().strip('"').strip("'")
    if mobile_path:
        mobile_result = uploader.upload(file_path=mobile_path, platform="stb-mobile")
        print(f"Sonuç:\n{mobile_result}\n")