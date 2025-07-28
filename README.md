# Mango DPP - Digital Product Platform for Fashion Teams

🎯 **Amaç (Purpose)**

Moda markalarının koleksiyon geliştirme, numune yönetimi ve tedarik zinciri koordinasyonunu uçtan uca dijitalleştirmek. Mango DPP, sürdürülebilir, hızlı ve API-uyumlu bir dijital ürün geliştirme platformudur.

## 🧩 Temel Özellikler

- **Koleksiyon Yönetimi**: Sezon bazlı koleksiyon yapıları, moodboard'lar, stil grupları
- **Numune & Fit Takibi**: Dijital numune kartları, revizyon geçmişi, teknik çizimler
- **Tedarikçi Portalı**: Gerçek zamanlı iş birliği, doküman paylaşımı
- **Karbon Ayak İzi Ölçümü**: Ürün bazında CO₂ salımı ölçümü
- **NFT Dijital Pasaport**: Blockchain tabanlı ürün kimliği ve QR kod entegrasyonu
- **Onay & Süreç Takibi**: Kanban style süreç yönetimi
- **Analitik & Dashboard**: KPI takibi, sürdürülebilirlik skorları

## 🌍 Teknoloji Altyapısı

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: HTML/CSS/JavaScript (Modern UI)
- **Blockchain**: Web3.py + Ethereum/Polygon
- **QR Kod**: Python QRCode library
- **Database**: PostgreSQL

## 🚀 Kurulum

```bash
# Virtual environment aktif et
source .venv/bin/activate

# Uygulamayı çalıştır
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

## 🎨 Tasarım Sistemi

### Renk Paleti
- **Ana Renk (Green)**: `#005530` - Sürdürülebilirlik ve doğa
- **İkincil Renk (Red)**: `#dc2626` - Uyarı ve kritik veriler  
- **Navy**: `#02154e` - Güven ve profesyonellik
- **Beyaz**: Ana arkaplan rengi
- **Gri Tonları**: Metin ve ikincil elemanlar

### Tipografi
- **Ana Font**: Arial (System Font)
- **Türkçe karakter desteği**: ğ, ü, ş, ı, ç, ö tam uyumlu
- **Font Güvenilirliği**: Tüm sistemlerde aynı görünüm

### Marka Entegrasyonu
- **Rabateks Logosu**: Header'da entegre edildi
- **Logo Formatı**: SVG (skalabilir)
- **Logo Bağlantısı**: rabateks.com'a yönlendirme

## 📱 Kullanım

1. Web tarayıcısında `http://localhost:8002` adresine git
2. Koleksiyon oluştur ("Sürdürülebilir Koleksiyon 2025")
3. Stil ekle (AI görsel oluşturma seçeneği ile)
4. NFT dijital pasaport oluştur
5. QR kod ile ürün takibi yap
6. Sürdürülebilirlik analizlerini incele:
   - Malzeme bazlı karbon analizi
   - Üretim lokasyonu analizi

## 🌟 **Gelişmiş Özellikler**

### 1. **AI Görsel Oluşturma**
- OpenAI DALL-E 3 entegrasyonu
- Stil tanımından otomatik ürün görseli
- Ürün fotoğrafları AI ile oluşturulur

### 2. **Detaylı Sürdürülebilirlik Analizi**
- **Malzeme Analizi**: `/sustainability/materials`
  - Sürdürülebilirlik skorları (1-10 ölçeği)
  - En iyi/en kötü malzemeler
  - Organik pamuk vs polyester karşılaştırması

- **Üretim Lokasyonu Analizi**: `/sustainability/production`  
  - Lokasyon bazlı karbon ayak izi
  - Taşıma mesafesi hesaplamaları
  - Türkiye, Çin, Hindistan karşılaştırması

### 3. **NFT Dijital Pasaport**
- Blockchain tabanlı ürün kimliği
- QR kod ile anında erişim
- Sertifika ve sürdürülebilirlik verileri
- Paylaşılabilir dijital pasaport

---
🤖 Generated with [Memex](https://memex.tech)