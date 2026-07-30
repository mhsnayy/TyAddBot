import requests
import urllib.parse
import datetime
import os
import time
from typing import Dict, Any, List, Optional

class TrendyolAssetUploader:
    def __init__(self, token: str):
        self.base_url = "https://apigw.trendyol.com/discovery-displayads-editorbff-service/upload/image"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def upload(self, file_path: str, platform: str = "stb-web") -> Optional[str]:
        if not os.path.exists(file_path):
            print(f"[HATA] Dosya bulunamadı: {file_path}")
            return None
            
        ext = os.path.splitext(file_path)[1].lower()
        url = f"{self.base_url}/{platform}"
        
        possible_form_keys = ['image', 'file', 'banner', 'upload', 'multipartFile', 'fileData']
        
        print(f"[{platform.upper()}] Yükleniyor... ({file_path})")
        
        for key in possible_form_keys:
            try:
                with open(file_path, 'rb') as f:
                    files = {key: (os.path.basename(file_path), f, f'image/{ext.replace(".", "")}')}
                    response = requests.post(url, headers=self.headers, files=files, timeout=15)
                    
                    if response.status_code in [200, 201]:
                        return response.json().get("absoluteUrl")
                    elif response.status_code == 400 and "Unexpected field" in response.text:
                        continue
                    else:
                        print(f" BAŞARISIZ (HTTP {response.status_code}): {response.text}")
                        return None
            except Exception as e:
                print(f" HATA: {e}")
                return None
                
        print(" [BAŞARISIZ] Olası tüm anahtar kelimeler denendi ama kabul edilmedi.")
        return None

class TrendyolAdSlotScanner:
    def __init__(self, token: str, merchant_id: str, rb_id: str):
        self.base_url = "https://apigw.trendyol.com/discovery-displayads-editorbff-service"
        self.merchant_id = merchant_id
        self.rb_id = rb_id
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Connection": "keep-alive"
        })

    def fetch_all_keywords_calendar(self, keyword: str) -> Optional[List[Dict[str, Any]]]:
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
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 429:
                return [] 
                
            response.raise_for_status()
            return self._extract_all_slots(response.json())
        except Exception:
            return None

    def _extract_all_slots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        parsed_slots = []
        keywords_data = data.get("keywords", [])
        
        for api_index, item in enumerate(keywords_data):
            current_keyword = item.get("keyword")
            normalized_kw = item.get("normalizedKeyword")
            volume_range = item.get("volumeRange", {})
            max_volume = volume_range.get("max", 0)
            slots = item.get("slots", {})
            
            for date_key, details in slots.items():
                parsed_slots.append({
                    "keyword": current_keyword,
                    "normalizedKeyword": normalized_kw,
                    "date": date_key,
                    "price": details.get("price", 0),
                    "is_hold": details.get("isHold", True),
                    "max_volume": max_volume,
                    "api_order": api_index
                })
        return parsed_slots

    def buy_ad_slot(self, slot_data: Dict[str, Any], web_cdn_url: str, mobile_cdn_url: str) -> bool:
        url = f"{self.base_url}/top-banner-a"
        current_time_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        campaign_name = f"Banner-{current_time_str}"
        redirection_link = f"https://www.trendyol.com/sr?rb={self.rb_id}&mid={self.merchant_id}"

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

        print(f"\n[POST İSTEĞİ] Tetiğe basıldı! Satın alma yollanıyor...")

        try:
            response = self.session.post(url, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                response_data = response.json()
                hold_failures = response_data.get("holdFailures", [])
                
                if len(hold_failures) == 0:
                    advert_id = response_data.get("advert", {}).get("advertId", "Bilinmiyor")
                    print(f"[BAŞARILI] Reklam başarıyla alındı! Advert ID: {advert_id}")
                    return True
                else:
                    print(f"[YARIŞ KAYBEDİLDİ] İstek gitti ama bizden önce bir bot slotu kaptı!")
                    print(f"Hata Detayları: {hold_failures}")
                    return False
            else:
                print(f"[BAŞARISIZ] HTTP Status: {response.status_code}")
                print(f"Detay: {response.text}")
                return False

        except Exception as e:
            print(f"[HATA] İstek sırasında bir sorun oluştu: {e}")
            return False

def main():
    print("="*60)
    print("GİRİŞ BİLGİLERİ")
    print("="*60)
    
    raw_token = input("Lütfen Trendyol Bearer Token'ınızı girin:\n> ").strip()
    if not raw_token:
        print("HATA: Token boş bırakılamaz. Program kapatılıyor.")
        time.sleep(3)
        return
        
    if raw_token.lower().startswith("bearer "):
        raw_token = raw_token[7:].strip()
    
    merchant_input = input("Merchant ID (Erbatab için boş bırakıp Enter'a basın): ").strip()
    MERCHANT_ID = merchant_input if merchant_input else "679772"
    
    rb_input = input("RB ID (Erbatab için boş bırakıp Enter'a basın): ").strip()
    RB_ID = rb_input if rb_input else "1742546"

    uploader = TrendyolAssetUploader(token=raw_token)
    scanner = TrendyolAdSlotScanner(token=raw_token, merchant_id=MERCHANT_ID, rb_id=RB_ID)

    while True:
        print("\n" + "="*60)
        print("TRENDYOL REKLAM OTOMASYONU")
        print("="*60)
        print("[1] BOT ÇALIŞTIR")
        print("[0] Çıkış")
        print("="*60)
        
        main_choice = input("Seçiminiz: ").strip()

        if main_choice == '0':
            print("Program kapatılıyor. Görüşmek üzere!")
            time.sleep(2)
            break

        elif main_choice == '1':
            print("\n--- ZAMAN AYARLI KESKİN NİŞANCI MODU (STRICT LOCK) ---")
            
            web_path = input("WEB görselinin YEREL dosya yolu: ").strip().strip('"').strip("'")
            mob_path = input("MOBİL görselinin YEREL dosya yolu: ").strip().strip('"').strip("'")
            
            if not web_path or not mob_path:
                print("HATA: İşlem için Web ve Mobil görsellerinin yolları zorunludur!")
                continue

            target_keyword = input("🔎 Taramak istediğiniz anahtar kelime: ").strip()
            if not target_keyword:
                print("HATA: Anahtar kelime boş bırakılamaz!")
                continue
            
            # ARKA PLANDA YÜKLEME İŞLEMİ
            print("\n[HAZIRLIK] Yerel görseller CDN'e aktarılıyor")
            
            web_banner_url = uploader.upload(file_path=web_path, platform="stb-web")
            if not web_banner_url:
                print("HATA: Web görseli yüklenemedi. Operasyon iptal edildi.")
                continue
                
            mob_banner_url = uploader.upload(file_path=mob_path, platform="stb-mobile")
            if not mob_banner_url:
                print("HATA: Mobil görseli yüklenemedi. Operasyon iptal edildi.")
                continue

            print("\nCDN linkleri oluşturuldu.")
            
            # PUSU PARAMETRELERİ
            duration_minutes = 2
            delay_seconds = 0.5 
            end_time = time.time() + (duration_minutes * 60)
            attempt_count = 0
            
            print(f"\n '{target_keyword}' kelimesi için HEDEF KİLİDİ açıldı.")
            print(f"Kural: YALNIZCA API'nin 0. index verdiği kelime taranacak.")
            print(f"Süre: {duration_minutes} dakika boyunca tarama yapılacak.\n")

            target_acquired = False

            while time.time() < end_time:
                attempt_count += 1
                print(f"\rDeneme: {attempt_count} | API sorgulanıyor...", end="", flush=True)
                
                all_slots = scanner.fetch_all_keywords_calendar(keyword=target_keyword)
                
                if all_slots:
                    top_keyword_slots = [s for s in all_slots if s['api_order'] == 0]
                    
                    available_slots = [s for s in top_keyword_slots if not s['is_hold']]
                    
                    if available_slots:
                        print(f"\n\n [{attempt_count}. Deneme] HEDEFTE (0. SIRA) BOŞ SLOT TESPİT EDİLDİ!")
                        
                        available_slots.sort(key=lambda x: x['date'], reverse=True)
                        target_slot = available_slots[0]
                        
                        print("="*50)
                        print(f"Seçilen Varyasyon : {target_slot['keyword']} (API Sıra: 0)")
                        print(f"Tarih             : {target_slot['date']}")
                        print(f"Fiyat             : {target_slot['price']} TL")
                        print("="*50)
                        
                        scanner.buy_ad_slot(slot_data=target_slot, web_cdn_url=web_banner_url, mobile_cdn_url=mob_banner_url)
                        target_acquired = True
                        break 
                
                time.sleep(delay_seconds)

            if not target_acquired:
                print(f"\n\n ZAMAN AŞIMI: {duration_minutes} dakika doldu.")
                print(f"Toplam {attempt_count} istek atıldı ancak 0. sıradaki kelime için hiç boş slot düşmedi.")
            
            input("\nDevam etmek için Enter'a basın...")
            
        else:
            print("Hatalı seçim! Lütfen geçerli bir numara girin.")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        import os
        os.system('chcp 65001 > nul')
        
    try:
        main()
    except Exception as e:
        print(f"\nBeklenmeyen bir hata oluştu: {e}")
        input("Çıkmak için Enter'a basın...")