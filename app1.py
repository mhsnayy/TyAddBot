import requests
import urllib.parse
import datetime
from typing import Dict, Any, List, Optional
import os

class TrendyolAdSlotScanner:
    def __init__(self, token: str, merchant_id: str, rb_id: str):
        self.base_url = "https://apigw.trendyol.com/discovery-displayads-editorbff-service"
        self.headers_json = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Upload işlemi için Content-Type requests tarafından otomatik (multipart/form-data) belirlenmeli
        self.headers_upload = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.merchant_id = merchant_id
        self.rb_id = rb_id

    def upload_banner_image(self, file_path: str, platform: str = "stb-web") -> Optional[str]:
        """
        Yerel bir resmi Trendyol'a yükler ve CDN linkini döner.
        platform: 'stb-web' veya 'stb-mobile' olabilir.
        Not: Hız için bu metodu sürekli kullanmak yerine CDN linklerini sabitlemek daha iyidir.
        """
        url = f"{self.base_url}/upload/image/{platform}"
        
        if not os.path.exists(file_path):
            print(f"[HATA] Dosya bulunamadı: {file_path}")
            return None

        print(f"[{platform.upper()}] Resmi Trendyol'a yükleniyor...")
        
        try:
            with open(file_path, 'rb') as file_data:
                files = {'file': file_data} 
                response = requests.post(url, headers=self.headers_upload, files=files, timeout=15)
                
                response.raise_for_status()
                data = response.json()
                
                cdn_url = data.get("absoluteUrl")
                if cdn_url:
                    print(f"✅ Başarılı! CDN Linki: {cdn_url}")
                    return cdn_url
                return None
        except Exception as e:
            print(f"❌ [HATA] Resim yükleme başarısız: {e}")
            return None

    def fetch_all_keywords_calendar(self, keyword: str) -> Optional[List[Dict[str, Any]]]:
        """Tüm takvimi çeker."""
        params = {
            "searchTerm": keyword,
            "size": 10,
            "page": 1,
            "sortOrder": "desc",
            "isSlotUpdate": "false",
            "rb[]": self.rb_id,
            "mid[]": self.merchant_id
        }
        
        query_string = urllib.parse.urlencode(params, doseq=True)
        url = f"{self.base_url}/search/keyword-slots?{query_string}"

        try:
            response = requests.get(url, headers=self.headers_json, timeout=5)
            response.raise_for_status()
            return self._extract_all_slots(response.json())
        except Exception as e:
            print(f"[HATA] Takvim çekilemedi: {e}")
            return None

    def _extract_all_slots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        parsed_slots = []
        keywords_data = data.get("keywords", [])
        
        for item in keywords_data:
            current_keyword = item.get("keyword")
            normalized_kw = item.get("normalizedKeyword")
            slots = item.get("slots", {})
            
            for date_key, details in slots.items():
                parsed_slots.append({
                    "keyword": current_keyword,
                    "normalizedKeyword": normalized_kw,
                    "date": date_key,
                    "price": details.get("price", 0),
                    "is_hold": details.get("isHold", True)
                })
        return parsed_slots

    def buy_ad_slot(self, slot_data: Dict[str, Any], web_cdn_url: str, mobile_cdn_url: str) -> bool:
        """Kullanıcının seçtiği slot için satın alma payload'unu yollar."""
        url = f"{self.base_url}/top-banner-a"
        
        current_time_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        campaign_name = f"Banner-{current_time_str}"
        redirection_link = f"https://www.trendyol.com/sr?rb={self.rb_id}&mid={self.merchant_id}"

        # Gönderdiğin Payload formatı ile birebir aynı yapı
        payload = {
            "name": campaign_name,
            "redirectionLink": redirection_link,
            "banners": {
                "mobile": mobile_cdn_url,
                "web": web_cdn_url
            },
            "slots": [
                {
                    "normalizedKeyword": slot_data["normalizedKeyword"],
                    "price": slot_data["price"],
                    "date": slot_data["date"]
                }
            ]
        }

        print(f"\n[İŞLEM] Trendyol'a satın alma isteği gönderiliyor...")

        try:
            response = requests.post(url, headers=self.headers_json, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                response_data = response.json()
                hold_failures = response_data.get("holdFailures", [])
                
                if len(hold_failures) == 0:
                    advert_id = response_data.get("advert", {}).get("advertId", "Bilinmiyor")
                    print(f"✅ [BAŞARILI] Reklam alındı! Advert ID: {advert_id}")
                    return True
                else:
                    # Status 200 döndü ama reklamı alamadık (Race Condition kaybettik)
                    print(f"⚠️ [YARIŞ KAYBEDİLDİ] İstek gitti ama slot başkasına rezerve edilmiş!")
                    print(f"Hata Detayları: {hold_failures}")
                    return False
            else:
                print(f"❌ [BAŞARISIZ] HTTP Status: {response.status_code}")
                print(f"Detay: {response.text}")
                return False

        except Exception as e:
            print(f"❌ [HATA] İstek sırasında bir sorun oluştu: {e}")
            return False


if __name__ == "__main__":
    # KİMLİK BİLGİLERİ
    TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3ODU0MDExMDAsImV4cCI6MTc4NTQ4NzUwMCwiZW1haWwiOiJlcmJhdGFiQGdtYWlsLmNvbSIsInVzZXJJZCI6MjIwMSwicGVybWlzc2lvbnMiOlt7ImlkIjoxLCJuYW1lIjoiY2FuVmlld01QUmVwb3J0cyJ9LHsiaWQiOjQsIm5hbWUiOiJjYW5WaWV3QWNjb3VudERldGFpbCJ9LHsiaWQiOjc0LCJuYW1lIjoiY2FuVmlld1Byb2R1Y3RVcGRhdGUifSx7ImlkIjozNSwibmFtZSI6ImNhblZpZXdDb3Vwb24ifSx7ImlkIjo4MSwibmFtZSI6ImNhblZpZXdEaXNwbGF5QWRzIn0seyJpZCI6ODIsIm5hbWUiOiJjYW5WaWV3SW5mbHVlbmNlckFkcyJ9LHsiaWQiOjcyLCJuYW1lIjoiY2FuVmlld0FkcyJ9LHsiaWQiOjc2LCJuYW1lIjoiY2FuVmlld1Byb2R1Y3RBZHMifSx7ImlkIjo3NywibmFtZSI6ImNhblZpZXdCYW5uZXJBZHMifSx7ImlkIjo3OCwibmFtZSI6ImNhblZpZXdUdk91dGRvb3JBZHMifSx7ImlkIjoyLCJuYW1lIjoiY2FuVmlld0xpbmtzIn0seyJpZCI6NzMsIm5hbWUiOiJjYW5WaWV3RmluYW5jZSJ9LHsiaWQiOjgzLCJuYW1lIjoiY2FuVmlld1N0b3JlQWRzIn0seyJpZCI6MTI0LCJuYW1lIjoiY2FuVmlld1NlZ21lbnRzIn0seyJpZCI6ODAsIm5hbWUiOiJjYW5WaWV3TGlua1JlcG9ydHMifV0sImNvbnRhY3ROYW1lIjoiWmFmZXIiLCJjb250YWN0U3VybmFtZSI6IkF2aW5kaWsiLCJhY2NvdW50SWQiOjExNzMsImFjY291bnROYW1lIjoiRXJiYXRhYiIsImNhblZpZXdEaXN0cmlidXRvckJhc2VkUmVwb3J0IjpmYWxzZX0.M-IQjZYEGoAlKKJtrynDeUSF6Ei3rKNWHtX0ZuH_U_Y"
    MERCHANT_ID = "679772"
    RB_ID = "1742546"
    
    # SABİTLENMİŞ CDN LİNKLERİ (Botun hızlı olması için manuel olarak buraya koyuyoruz)
    # Eğer yenilemek istersen scanner.upload_banner_image(...) metodunu kullanabilirsin.
    WEB_BANNER = "https://cdn.dsmcdn.com/display-ads/brand-ads/images/stb-web_1173_4adc2852-631a-46cf-b5cf-8d25adcc2914.png"
    MOBILE_BANNER = "https://cdn.dsmcdn.com/display-ads/brand-ads/images/stb-mobile_1173_4d3fee48-ce61-4072-b1ee-523d15cfc6a4.png"
    
    scanner = TrendyolAdSlotScanner(token=TOKEN, merchant_id=MERCHANT_ID, rb_id=RB_ID)
    
    while True:
        target_keyword = input("\n🔎 Taramak istediğiniz kelimeyi girin (Çıkmak için 'q'): ").strip()
        if target_keyword.lower() == 'q': break
        if not target_keyword: continue
            
        print(f"\nTakvim çekiliyor...")
        all_slots = scanner.fetch_all_keywords_calendar(keyword=target_keyword)
        
        if not all_slots:
            print("❌ Bu kelime API'de bulunamadı.")
            continue
            
        # Sadece boş (is_hold=False) olanları filtrele
        available_slots = [slot for slot in all_slots if not slot['is_hold']]
        
        if not available_slots:
            print("\n🔴 TAKVİM DOLU: Bu kelime için tüm varyasyonlardaki slotlar alınmış.")
            continue
            
        print("\n✅ SATIN ALINABİLİR BOŞ SLOTLAR:")
        print("="*60)
        for idx, slot in enumerate(available_slots, start=1):
            print(f"[{idx}] KELİME: {slot['keyword']:<15} | TARİH: {slot['date']} | FİYAT: {slot['price']} TL")
        print("="*60)
        
        choice = input(f"\nSatın almak istediğiniz slotun numarasını girin (İptal için 0): ").strip()
        
        if choice == '0' or not choice.isdigit():
            print("İşlem iptal edildi.")
            continue
            
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(available_slots):
            selected_slot = available_slots[choice_idx]
            print(f"\nSeçilen: {selected_slot['keyword']} | {selected_slot['date']} ({selected_slot['price']} TL)")
            confirm = input("Bu slotu SATIN ALMAK istiyor musunuz? (E/H): ").strip().upper()
            
            if confirm == 'E':
                # Satın alma işlemini başlat, hazırladığımız sabit CDN linklerini gönder
                scanner.buy_ad_slot(selected_slot, web_cdn_url=WEB_BANNER, mobile_cdn_url=MOBILE_BANNER)
            else:
                print("Satın alma iptal edildi.")
        else:
            print("Geçersiz numara!")