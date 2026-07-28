import requests
import urllib.parse
from typing import List, Dict, Any

class TrendyolAdSlotScanner:
    def __init__(self, token: str, merchant_id: str, rb_id: str):
        self.base_url = "https://apigw.trendyol.com/discovery-displayads-editorbff-service/search/keyword-slots"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.merchant_id = merchant_id
        self.rb_id = rb_id

    def fetch_available_slots(self, keyword: str, page: int = 1, size: int = 10) -> List[Dict[str, Any]]:
        """
        Belirtilen keyword için API'ye istek atar ve isHold=False olan slotları hacim bilgisiyle döndürür.
        """
        params = {
            "searchTerm": keyword,
            "size": size,
            "page": page,
            "sortOrder": "desc",
            "isSlotUpdate": "false",
            "rb[]": self.rb_id,
            "mid[]": self.merchant_id
        }
        
        query_string = urllib.parse.urlencode(params, doseq=True)
        url = f"{self.base_url}?{query_string}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 401:
                raise Exception("Token expired (401). Yeni token gerekiyor.")
            elif response.status_code == 429:
                raise Exception("Rate limit (429). Çok hızlı istek atıyorsun.")
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_slots(data)

        except requests.exceptions.RequestException as e:
            print(f"[HATA] API İsteği başarısız: {e}")
            return []
        except ValueError:
            print("[HATA] Yanıt JSON formatında değil. WAF'a takılmış olabiliriz.")
            return []

    def _parse_slots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Gelen JSON'u dekonstrükte eder, volume bilgisini alır ve isHold == False olanları filtreler.
        """
        available_slots = []
        
        keywords_data = data.get("keywords", [])
        for item in keywords_data:
            current_keyword = item.get("keyword")
            
            # Hacim bilgisini güvenli (fallback'li) bir şekilde çıkarıyoruz
            volume_range = item.get("volumeRange", {})
            min_volume = volume_range.get("min", 0)
            max_volume = volume_range.get("max", 0)
            
            slots = item.get("slots", {})
            
            for date_key, details in slots.items():
                is_hold = details.get("isHold", True)
                
                if not is_hold:
                    available_slots.append({
                        "keyword": current_keyword,
                        "date": date_key,
                        "price": details.get("price", 0),
                        "search_volume_min": min_volume,
                        "search_volume_max": max_volume
                    })
                    
        return available_slots

# --- Kullanım Senaryosu ---
if __name__ == "__main__":
    TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3ODUyNDc1NDYsImV4cCI6MTc4NTMzMzk0NiwiZW1haWwiOiJlcmJhdGFiQGdtYWlsLmNvbSIsInVzZXJJZCI6MjIwMSwicGVybWlzc2lvbnMiOlt7ImlkIjoxLCJuYW1lIjoiY2FuVmlld01QUmVwb3J0cyJ9LHsiaWQiOjQsIm5hbWUiOiJjYW5WaWV3QWNjb3VudERldGFpbCJ9LHsiaWQiOjc0LCJuYW1lIjoiY2FuVmlld1Byb2R1Y3RVcGRhdGUifSx7ImlkIjozNSwibmFtZSI6ImNhblZpZXdDb3Vwb24ifSx7ImlkIjo4MSwibmFtZSI6ImNhblZpZXdEaXNwbGF5QWRzIn0seyJpZCI6ODIsIm5hbWUiOiJjYW5WaWV3SW5mbHVlbmNlckFkcyJ9LHsiaWQiOjcyLCJuYW1lIjoiY2FuVmlld0FkcyJ9LHsiaWQiOjc2LCJuYW1lIjoiY2FuVmlld1Byb2R1Y3RBZHMifSx7ImlkIjo3NywibmFtZSI6ImNhblZpZXdCYW5uZXJBZHMifSx7ImlkIjo3OCwibmFtZSI6ImNhblZpZXdUdk91dGRvb3JBZHMifSx7ImlkIjoyLCJuYW1lIjoiY2FuVmlld0xpbmtzIn0seyJpZCI6NzMsIm5hbWUiOiJjYW5WaWV3RmluYW5jZSJ9LHsiaWQiOjgzLCJuYW1lIjoiY2FuVmlld1N0b3JlQWRzIn0seyJpZCI6MTI0LCJuYW1lIjoiY2FuVmlld1NlZ21lbnRzIn0seyJpZCI6ODAsIm5hbWUiOiJjYW5WaWV3TGlua1JlcG9ydHMifV0sImNvbnRhY3ROYW1lIjoiWmFmZXIiLCJjb250YWN0U3VybmFtZSI6IkF2aW5kaWsiLCJhY2NvdW50SWQiOjExNzMsImFjY291bnROYW1lIjoiRXJiYXRhYiIsImNhblZpZXdEaXN0cmlidXRvckJhc2VkUmVwb3J0IjpmYWxzZX0.b2T_z8XcaiPBDPZlI1zsBX7rOBrDIBZrW6dSBDlr-Lo"
    MERCHANT_ID = "679772"
    RB_ID = "1742546"
    TARGET_KEYWORD = "magnezyum"

    scanner = TrendyolAdSlotScanner(token=TOKEN, merchant_id=MERCHANT_ID, rb_id=RB_ID)
    
    print(f"'{TARGET_KEYWORD}' için boş reklam slotları aranıyor...")
    available_slots = scanner.fetch_available_slots(keyword=TARGET_KEYWORD)
    
    if available_slots:
        print(f"\n[{len(available_slots)} adet] boş slot bulundu!\n")
        for slot in available_slots:
            print(f"Tarih: {slot['date']}")
            print(f"  ├─ Anahtar Kelime: {slot['keyword']}")
            print(f"  ├─ Fiyat: {slot['price']} TL")
            print(f"  └─ Tahmini Hacim: {slot['search_volume_min']} - {slot['search_volume_max']} arama\n")
    else:
        print("\nŞu an için boş/alınabilir (isHold=False) slot bulunamadı veya bir hata oluştu.")