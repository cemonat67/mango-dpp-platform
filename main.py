from fastapi import FastAPI, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import urllib.parse
from sqlalchemy.orm import Session
import qrcode
import io
import base64
import json
import uuid
from datetime import datetime
from typing import Optional, List
import os
from web3 import Web3
from eth_account import Account
import hashlib
import openai
import keyring
import asyncio
import aiohttp

# Database imports
from database import get_db, init_db
from models import Collection, Style, NFTPassport, Supplier
from translations import get_text, get_all_texts

app = FastAPI(title="Mango DPP - Digital Product Platform")

# CORS ve encoding ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files ve templates
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
init_db()

def fix_turkish_encoding(text):
    """Fix Turkish character encoding issues"""
    if not text:
        return text
    
    # Common Turkish character fixes - comprehensive mapping
    replacements = {
        'Ä°': 'İ',  # Capital I with dot
        'Ä±': 'ı',  # Lowercase dotless i
        'Ã¼': 'ü',  # u with umlaut
        'Ã–': 'Ö',  # Capital O with umlaut
        'Ã¶': 'ö',  # o with umlaut
        'Ã‡': 'Ç',  # Capital C with cedilla
        'Ã§': 'ç',  # c with cedilla
        'Åž': 'Ş',  # Capital S with cedilla
        'ÅŸ': 'ş',  # s with cedilla
        'Å ': 'Ş',  # Alternative Capital S with cedilla
        'Å¡': 'ş',  # Alternative s with cedilla
        'Åı': 'Şı', # Specific combination
        'Åık': 'Şık', # Common word
        'Äž': 'Ğ',  # Capital G with breve
        'ÄŸ': 'ğ',  # g with breve
        'GÃ¶z': 'Göz',  # Common word
        'alÄ±cÄ±': 'alıcı',  # Common word
    }
    
    fixed_text = text
    for wrong, correct in replacements.items():
        fixed_text = fixed_text.replace(wrong, correct)
    
    return fixed_text

class MangoDPP:
    def __init__(self):
        self.setup_ai_client()
    
    def get_collections(self, db: Session):
        return db.query(Collection).all()
    
    def get_styles(self, db: Session):
        return db.query(Style).all()
    
    def get_nfts(self, db: Session):
        return db.query(NFTPassport).all()
        
    def generate_qr_code(self, data: str) -> str:
        """QR kod oluştur ve base64 string olarak döndür"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def create_nft_passport(self, product_data: dict) -> dict:
        """NFT dijital pasaport oluştur"""
        nft_id = str(uuid.uuid4())
        
        # NFT metadata
        nft_data = {
            "id": nft_id,
            "product_code": product_data.get("code", ""),
            "name": product_data.get("name", ""),
            "collection": product_data.get("collection", ""),
            "materials": product_data.get("materials", []),
            "production_location": product_data.get("production_location", ""),
            "carbon_footprint": product_data.get("carbon_footprint", 0),
            "certificates": product_data.get("certificates", []),
            "supplier": product_data.get("supplier", ""),
            "created_at": datetime.now().isoformat(),
            "blockchain_hash": hashlib.sha256(nft_id.encode()).hexdigest()
        }
        
        # QR kod oluştur
        qr_data = f"https://mangodpp.com/passport/{nft_id}"
        nft_data["qr_code"] = self.generate_qr_code(qr_data)
        nft_data["qr_url"] = qr_data
        
        # NFT data is now stored in database by the route handler
        return nft_data
    
    def setup_ai_client(self):
        """AI client kurulumu"""
        try:
            # Environment variable'dan al (cloud deployment için)
            api_key = os.getenv("OPENAI_API_KEY")
            
            # Keyring'den OpenAI API key'i al (local development için)
            if not api_key:
                for key_name in ['OPENAI_API_KEY', 'openai_api_key', 'openai-api-key']:
                    try:
                        api_key = keyring.get_password("memex", key_name)
                        if api_key:
                            break
                    except:
                        continue
            
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                self.ai_enabled = True
            else:
                self.ai_enabled = False
                print("OpenAI API key bulunamadı. AI görsel oluşturma devre dışı.")
        except Exception as e:
            self.ai_enabled = False
            print(f"AI client kurulum hatası: {e}")
    
    async def generate_product_image(self, style_data: dict) -> Optional[str]:
        """AI ile ürün görseli oluştur"""
        if not self.ai_enabled:
            return None
            
        try:
            # Ürün tanımını oluştur
            prompt = self.create_image_prompt(style_data)
            
            # OpenAI DALL-E ile görsel oluştur
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Görsel URL'sini al
            image_url = response.data[0].url
            
            # Görseli indir ve kaydet
            image_path = await self.download_and_save_image(image_url, style_data["id"])
            
            return image_path
            
        except Exception as e:
            error_message = str(e)
            print(f"AI görsel oluşturma hatası: {e}")
            
            # Provide more specific error info
            if "invalid_api_key" in error_message or "401" in error_message:
                print("OpenAI API key geçersiz veya süresi dolmuş")
            elif "billing" in error_message or "quota" in error_message:
                print("OpenAI hesap bakiyesi yetersiz veya kota aşıldı")
            
            return None
    
    def create_image_prompt(self, style_data: dict) -> str:
        """Stil verilerinden görsel prompt'u oluştur"""
        category = style_data.get("category", "giyim")
        materials = ", ".join(style_data.get("materials", []))
        name = style_data.get("name", "ürün")
        
        # Kategori bazlı prompt oluştur
        category_prompts = {
            "Üst Giyim": "fashionable top, shirt, blouse, sweater",
            "Alt Giyim": "stylish pants, trousers, jeans, skirt",
            "Elbise": "elegant dress, fashionable dress",
            "Dış Giyim": "jacket, coat, outerwear",
            "Aksesuar": "fashion accessory, bag, scarf"
        }
        
        base_prompt = category_prompts.get(category, "fashion item")
        
        prompt = f"""
        Professional fashion photography of a {base_prompt} called '{name}'.
        Made from {materials}.
        Clean white background, studio lighting, high-quality fashion photography.
        Modern, sustainable fashion design.
        Commercial product photography style.
        No text or watermarks.
        """
        
        return prompt.strip()
    
    async def download_and_save_image(self, image_url: str, style_id: str) -> str:
        """Görseli indir ve kaydet"""
        try:
            os.makedirs("static/images", exist_ok=True)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Dosya yolunu oluştur
                        filename = f"product_{style_id}.png"
                        filepath = f"static/images/{filename}"
                        
                        # Dosyayı kaydet
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                        
                        return f"/static/images/{filename}"
            
        except Exception as e:
            print(f"Görsel indirme hatası: {e}")
            return None
    
    def calculate_carbon_footprint(self, materials: List[str], production_location: str, transport: str) -> float:
        """Karbon ayak izi hesapla (basitleştirilmiş)"""
        base_carbon = 2.5  # kg CO2
        
        # Malzeme bazlı katsayılar
        material_factors = {
            "pamuk": 1.2,
            "polyester": 2.1,
            "yün": 3.8,
            "ipek": 2.9,
            "keten": 0.9,
            "organik_pamuk": 0.8
        }
        
        # Lokasyon bazlı katsayılar
        location_factors = {
            "türkiye": 1.0,
            "hindistan": 1.8,
            "çin": 2.2,
            "bangladeş": 1.9,
            "vietnam": 1.7
        }
        
        material_carbon = sum([material_factors.get(mat.lower(), 1.0) for mat in materials])
        location_carbon = location_factors.get(production_location.lower(), 1.0)
        
        total_carbon = base_carbon * material_carbon * location_carbon
        return round(total_carbon, 2)

mango_dpp = MangoDPP()

def get_language(request: Request) -> str:
    """Get current language from cookie or default to Turkish"""
    return request.cookies.get("language", "tr")

@app.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Ana dashboard"""
    lang = get_language(request)
    collections = mango_dpp.get_collections(db)
    styles = mango_dpp.get_styles(db)
    nfts = mango_dpp.get_nfts(db)
    
    stats = {
        "total_collections": len(collections),
        "total_styles": len(styles),
        "total_samples": 0,  # Placeholder
        "total_nfts": len(nfts)
    }
    
    response = templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "stats": stats,
        "collections": collections[:5],
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.post("/set-language")
async def set_language(language: str = Form(...)):
    """Set language preference"""
    response = JSONResponse({"success": True, "language": language})
    response.set_cookie("language", language, max_age=31536000)  # 1 year
    return response

@app.get("/collections")
async def collections_page(request: Request, db: Session = Depends(get_db)):
    """Koleksiyonlar sayfası"""
    lang = get_language(request)
    collections = mango_dpp.get_collections(db)
    response = templates.TemplateResponse("collections.html", {
        "request": request,
        "collections": collections,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.post("/collections")
async def create_collection(
    name: str = Form(...),
    season: str = Form(...),
    year: int = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """Yeni koleksiyon oluştur"""
    collection_id = str(uuid.uuid4())
    
    # Fix Turkish character encoding
    name = fix_turkish_encoding(name)
    season = fix_turkish_encoding(season)
    description = fix_turkish_encoding(description)
    
    collection = Collection(
        id=collection_id,
        name=name,
        season=season,
        year=year,
        description=description
    )
    
    db.add(collection)
    db.commit()
    db.refresh(collection)
    
    return JSONResponse({"success": True, "collection_id": collection_id})

@app.get("/collections/{collection_id}")
async def view_collection(request: Request, collection_id: str, db: Session = Depends(get_db)):
    """Koleksiyon detayını görüntüle"""
    lang = get_language(request)
    
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        return templates.TemplateResponse("404.html", {"request": request})
    
    # Get styles in this collection
    collection_styles = db.query(Style).filter(Style.collection_id == collection_id).all()
    
    response = templates.TemplateResponse("collection_detail.html", {
        "request": request,
        "collection": collection,
        "styles": collection_styles,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/collections/{collection_id}/edit")
async def edit_collection(request: Request, collection_id: str, db: Session = Depends(get_db)):
    """Koleksiyon düzenleme sayfası"""
    lang = get_language(request)
    
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        return templates.TemplateResponse("404.html", {"request": request})
    
    response = templates.TemplateResponse("collection_edit.html", {
        "request": request,
        "collection": collection,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.post("/collections/{collection_id}/edit")
async def update_collection(
    collection_id: str,
    name: str = Form(...),
    season: str = Form(...),
    year: int = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """Koleksiyon güncelle"""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        return JSONResponse({"error": "Collection not found"}, status_code=404)
    
    # Fix Turkish character encoding
    collection.name = fix_turkish_encoding(name)
    collection.season = fix_turkish_encoding(season)
    collection.year = year
    collection.description = fix_turkish_encoding(description)
    
    db.commit()
    return JSONResponse({"success": True})

@app.get("/styles")
async def styles_page(request: Request, db: Session = Depends(get_db)):
    """Stiller sayfası"""
    lang = get_language(request)
    styles = mango_dpp.get_styles(db)
    collections = mango_dpp.get_collections(db)
    
    response = templates.TemplateResponse("styles.html", {
        "request": request,
        "styles": styles,
        "collections": collections,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.post("/styles")
async def create_style(
    name: str = Form(...),
    collection_id: str = Form(...),
    category: str = Form(...),
    materials: str = Form(...),
    target_price: float = Form(...),
    production_location: str = Form(...),
    supplier: str = Form(...),
    generate_image: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Yeni stil oluştur"""
    style_id = str(uuid.uuid4())
    
    # Fix Turkish character encoding
    name = fix_turkish_encoding(name)
    category = fix_turkish_encoding(category)
    materials = fix_turkish_encoding(materials)
    production_location = fix_turkish_encoding(production_location)
    supplier = fix_turkish_encoding(supplier)
    
    materials_list = [m.strip() for m in materials.split(",")]
    
    # Karbon ayak izi hesapla
    carbon_footprint = mango_dpp.calculate_carbon_footprint(
        materials_list, production_location, "sea"
    )
    
    style = Style(
        id=style_id,
        name=name,
        collection_id=collection_id,
        category=category,
        materials=materials_list,
        target_price=target_price,
        production_location=production_location,
        supplier=supplier,
        carbon_footprint=carbon_footprint,
        status="tasarım"
    )
    
    # AI görsel oluştur (istenirse)
    if generate_image and mango_dpp.ai_enabled:
        try:
            # Style dict oluştur AI için
            style_dict = {
                "id": style_id,
                "name": name,
                "category": category,
                "materials": materials_list
            }
            image_path = await mango_dpp.generate_product_image(style_dict)
            if image_path:
                style.image_url = image_path
                style.status = "görsel_oluşturuldu"
        except Exception as e:
            print(f"Görsel oluşturma hatası: {e}")
    
    db.add(style)
    db.commit()
    db.refresh(style)
    
    return JSONResponse({
        "success": True, 
        "style_id": style_id,
        "image_generated": style.image_url is not None,
        "ai_enabled": mango_dpp.ai_enabled
    })

@app.post("/generate-image/{style_id}")
async def generate_style_image(style_id: str, db: Session = Depends(get_db)):
    """Var olan stil için AI görsel oluştur"""
    try:
        style = db.query(Style).filter(Style.id == style_id).first()
        if not style:
            return JSONResponse({"error": "Stil bulunamadı"}, status_code=404)
        
        if not mango_dpp.ai_enabled:
            return JSONResponse({"error": "AI görsel oluşturma devre dışı. OpenAI API key gerekli."}, status_code=400)
    
        # Create style data for AI generation
        style_data = {
            "id": style.id,
            "name": style.name,
            "materials": style.materials if style.materials else [],
            "category": style.category or "",
            "description": f"{style.name} made of {', '.join(style.materials) if style.materials else 'fabric'}"
        }
        
        image_path = await mango_dpp.generate_product_image(style_data)
        if image_path:
            style.image_url = image_path
            db.commit()
            
            return JSONResponse({
                "success": True,
                "image_url": image_path,
                "message": "Görsel başarıyla oluşturuldu"
            })
        else:
            # More specific error based on AI status
            if not mango_dpp.ai_enabled:
                return JSONResponse({"error": "OpenAI API key geçersiz veya eksik"}, status_code=500)
            else:
                return JSONResponse({"error": "Görsel oluşturulamadı - OpenAI API'de sorun olabilir"}, status_code=500)
            
    except Exception as e:
        error_message = str(e)
        if "invalid_api_key" in error_message or "401" in error_message:
            return JSONResponse({"error": "OpenAI API key geçersiz veya süresi dolmuş"}, status_code=401)
        elif "billing" in error_message or "quota" in error_message:
            return JSONResponse({"error": "OpenAI hesap bakiyesi yetersiz"}, status_code=402)
        else:
            return JSONResponse({"error": f"Görsel oluşturma hatası: {str(e)}"}, status_code=500)

@app.get("/passport/{nft_id}", response_class=HTMLResponse)
async def nft_passport(request: Request, nft_id: str, db: Session = Depends(get_db)):
    """NFT dijital pasaport görüntüle"""
    # Find NFT passport by its ID
    nft_passport = db.query(NFTPassport).filter(NFTPassport.id == nft_id).first()
    
    if not nft_passport:
        return templates.TemplateResponse("404.html", {"request": request})
    
    style = db.query(Style).filter(Style.id == nft_passport.style_id).first()
    collection = db.query(Collection).filter(Collection.id == style.collection_id).first() if style else None
    
    nft_data = {
        "id": nft_id,
        "name": style.name if style else "",
        "collection": collection.name if collection else "",
        "materials": style.materials if style and style.materials else [],
        "production_location": style.production_location if style else "",
        "carbon_footprint": style.carbon_footprint if style else 0,
        "certificates": nft_passport.certificates if nft_passport.certificates else [],
        "blockchain_hash": nft_passport.blockchain_hash,
        "qr_code": f"data:image/png;base64,{nft_passport.qr_code_data}" if nft_passport.qr_code_data else "",
        "qr_url": f"https://mango-dpp-platform-production.up.railway.app/passport/{nft_id}"
    }
    
    return templates.TemplateResponse("passport.html", {
        "request": request,
        "nft": nft_data
    })

@app.post("/generate-nft")
async def generate_nft_passport(
    style_id: str = Form(...),
    certificates: str = Form(""),
    additional_info: str = Form(""),
    db: Session = Depends(get_db)
):
    """Stil için NFT pasaport oluştur"""
    try:
        style = db.query(Style).filter(Style.id == style_id).first()
        if not style:
            return JSONResponse({"error": "Stil bulunamadı"}, status_code=404)
        
        collection = db.query(Collection).filter(Collection.id == style.collection_id).first()
    
        product_data = {
            "code": f"MNG-{style_id[:8]}",
            "name": style.name,
            "collection": collection.name if collection else "",
            "materials": style.materials if style.materials else [],
            "production_location": style.production_location or "",
            "carbon_footprint": style.carbon_footprint or 0,
            "certificates": [c.strip() for c in certificates.split(",") if c.strip()],
            "supplier": style.supplier or "",
            "additional_info": additional_info
        }
        
        nft_data = mango_dpp.create_nft_passport(product_data)
        
        # Create NFT passport in database
        nft_passport = NFTPassport(
            id=nft_data["id"],
            style_id=style.id,
            product_code=nft_data["product_code"],
            name=nft_data["name"],
            collection_name=nft_data["collection"],
            materials=nft_data["materials"],
            production_location=nft_data["production_location"],
            carbon_footprint=nft_data["carbon_footprint"],
            certificates=nft_data["certificates"],
            supplier=nft_data["supplier"],
            blockchain_hash=nft_data["blockchain_hash"],
            qr_code_data=nft_data["qr_code"],
            qr_url=nft_data["qr_url"],
            additional_info=additional_info
        )
        db.add(nft_passport)
        db.commit()
    
        return JSONResponse({
            "success": True,
            "nft_id": nft_data["id"],
            "qr_code": nft_data["qr_code"],
            "passport_url": nft_data["qr_url"]
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/sustainability")
async def sustainability_page(request: Request, db: Session = Depends(get_db)):
    """Sürdürülebilirlik dashboard"""
    lang = get_language(request)
    styles = mango_dpp.get_styles(db)
    
    total_carbon = sum([style.carbon_footprint or 0 for style in styles])
    avg_carbon = total_carbon / len(styles) if styles else 0
    
    # En düşük karbon ayak izli stiller
    low_carbon_styles = sorted(styles, key=lambda x: x.carbon_footprint or 0)[:5]
    
    # Karbon kategorilerine göre dağılım
    low_carbon_count = len([s for s in styles if (s.carbon_footprint or 0) < 3])
    medium_carbon_count = len([s for s in styles if 3 <= (s.carbon_footprint or 0) <= 5])
    high_carbon_count = len([s for s in styles if (s.carbon_footprint or 0) > 5])
    
    # Malzeme analizi
    material_analysis = {}
    for style in styles:
        for material in style.materials or []:
            if material not in material_analysis:
                material_analysis[material] = {"count": 0, "total_carbon": 0}
            material_analysis[material]["count"] += 1
            material_analysis[material]["total_carbon"] += style.carbon_footprint or 0
    
    # Ortalama karbon hesapla
    for material in material_analysis:
        material_analysis[material]["avg_carbon"] = round(
            material_analysis[material]["total_carbon"] / material_analysis[material]["count"], 2
        )
    
    response = templates.TemplateResponse("sustainability.html", {
        "request": request,
        "total_carbon": round(total_carbon, 2),
        "avg_carbon": round(avg_carbon, 2),
        "low_carbon_styles": low_carbon_styles,
        "total_styles": len(styles),
        "low_carbon_count": low_carbon_count,
        "medium_carbon_count": medium_carbon_count,
        "high_carbon_count": high_carbon_count,
        "material_analysis": material_analysis,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/sustainability/materials", response_class=HTMLResponse)
async def materials_analysis(request: Request, db: Session = Depends(get_db)):
    """Malzeme bazlı sürdürülebilirlik analizi"""
    lang = request.cookies.get("lang", "tr")
    material_stats = {}
    
    styles = mango_dpp.get_styles(db)
    for style in styles:
        materials = style.materials if style.materials else []
        for material in materials:
            if material not in material_stats:
                material_stats[material] = {
                    "styles": [],
                    "total_carbon": 0,
                    "avg_carbon": 0,
                    "usage_count": 0,
                    "sustainability_score": 0
                }
            
            material_stats[material]["styles"].append(style)
            material_stats[material]["total_carbon"] += style.carbon_footprint or 0
            material_stats[material]["usage_count"] += 1
    
    # Sürdürülebilirlik skorları (basitleştirilmiş)
    sustainability_scores = {
        "organik_pamuk": 9, "keten": 8, "yün": 6, "pamuk": 5,
        "ipek": 4, "polyester": 3, "naylon": 2, "akrilik": 1
    }
    
    for material in material_stats:
        if material_stats[material]["usage_count"] > 0:
            material_stats[material]["avg_carbon"] = round(
                material_stats[material]["total_carbon"] / material_stats[material]["usage_count"], 2
            )
        material_stats[material]["sustainability_score"] = sustainability_scores.get(
            material.lower(), 5
        )
    
    # En iyi ve en kötü malzemeler
    best_materials = sorted(
        material_stats.items(),
        key=lambda x: (x[1]["sustainability_score"], -x[1]["avg_carbon"]),
        reverse=True
    )[:5]
    
    worst_materials = sorted(
        material_stats.items(),
        key=lambda x: (x[1]["sustainability_score"], -x[1]["avg_carbon"])
    )[:5]
    
    response = templates.TemplateResponse("materials_analysis.html", {
        "request": request,
        "material_stats": material_stats,
        "best_materials": best_materials,
        "worst_materials": worst_materials,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/sustainability/production", response_class=HTMLResponse)
async def production_analysis(request: Request, db: Session = Depends(get_db)):
    """Üretim lokasyonu bazlı analiz"""
    lang = request.cookies.get("lang", "tr")
    location_stats = {}
    
    styles = mango_dpp.get_styles(db)
    for style in styles:
        location = style.production_location if style.production_location else "Bilinmiyor"
        if location not in location_stats:
            location_stats[location] = {
                "styles": [],
                "total_carbon": 0,
                "avg_carbon": 0,
                "count": 0
            }
        
        location_stats[location]["styles"].append(style)
        location_stats[location]["total_carbon"] += style.carbon_footprint or 0
        location_stats[location]["count"] += 1
    
    # Add sample production data if database is empty
    if not location_stats or len(location_stats) <= 1:
        sample_locations = {
            "Türkiye - İstanbul": {
                "styles": [],
                "total_carbon": 24.5,
                "avg_carbon": 4.1,
                "count": 6,
                "distance_km": 0,
                "transport_emission": 0,
                "energy_source": "50% Güneş + 50% Şebeke",
                "workforce": 180,
                "certifications": ["ISO 14001", "OEKO-TEX"],
                "efficiency_score": 85
            },
            "Türkiye - Bursa": {
                "styles": [],
                "total_carbon": 28.2,
                "avg_carbon": 4.7,
                "count": 6,
                "distance_km": 150,
                "transport_emission": 0.3,
                "energy_source": "25% Güneş + 75% Şebeke",
                "workforce": 240,
                "certifications": ["ISO 9001"],
                "efficiency_score": 78
            },
            "Türkiye - Denizli": {
                "styles": [],
                "total_carbon": 31.8,
                "avg_carbon": 5.3,
                "count": 6,
                "distance_km": 420,
                "transport_emission": 0.8,
                "energy_source": "15% Güneş + 85% Şebeke",
                "workforce": 320,
                "certifications": ["GOTS"],
                "efficiency_score": 72
            },
            "Bangladeş - Dhaka": {
                "styles": [],
                "total_carbon": 45.6,
                "avg_carbon": 7.6,
                "count": 6,
                "distance_km": 5200,
                "transport_emission": 12.4,
                "energy_source": "5% Güneş + 95% Şebeke",
                "workforce": 1500,
                "certifications": ["FairWear"],
                "efficiency_score": 58
            },
            "Çin - Guangzhou": {
                "styles": [],
                "total_carbon": 52.8,
                "avg_carbon": 8.8,
                "count": 6,
                "distance_km": 6800,
                "transport_emission": 16.2,
                "energy_source": "10% Güneş + 90% Şebeke",
                "workforce": 2200,
                "certifications": ["ISO 9001"],
                "efficiency_score": 62
            },
            "Vietnam - Ho Chi Minh": {
                "styles": [],
                "total_carbon": 48.4,
                "avg_carbon": 8.1,
                "count": 6,
                "distance_km": 8200,
                "transport_emission": 19.6,
                "energy_source": "8% Güneş + 92% Şebeke",
                "workforce": 800,
                "certifications": ["OEKO-TEX"],
                "efficiency_score": 65
            }
        }
        location_stats.update(sample_locations)
    else:
        # Add additional details to existing locations
        for location in location_stats:
            if location_stats[location]["count"] > 0:
                location_stats[location]["avg_carbon"] = round(
                    location_stats[location]["total_carbon"] / location_stats[location]["count"], 2
                )
    
    # En iyi ve en kötü lokasyonlar
    best_locations = sorted(
        location_stats.items(),
        key=lambda x: x[1]["avg_carbon"]
    )[:5]
    
    worst_locations = sorted(
        location_stats.items(),
        key=lambda x: x[1]["avg_carbon"],
        reverse=True
    )[:5]
    
    response = templates.TemplateResponse("production_analysis.html", {
        "request": request,
        "location_stats": location_stats,
        "best_locations": best_locations,
        "worst_locations": worst_locations,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/sustainability/carbon-followup", response_class=HTMLResponse)
async def carbon_followup(request: Request, db: Session = Depends(get_db)):
    """Konfeksiyon üreticisi karbon takibi"""
    lang = request.cookies.get("lang", "tr")
    styles = mango_dpp.get_styles(db)
    
    # Aylık karbon emisyonu verisi (örnek data)
    current_month_emissions = sum([style.carbon_footprint or 0 for style in styles])
    yearly_target = current_month_emissions * 12 * 0.8  # %20 azaltım hedefi
    reduction_progress = min(95, (yearly_target - current_month_emissions * 12) / yearly_target * 100) if yearly_target > 0 else 0
    
    # Enerji karışımı (örnek data)
    energy_mix = {
        "solar_power": 35,
        "grid_electricity": 50,
        "natural_gas": 15
    }
    
    # Su kullanımı ve kimyasal kullanımı (örnek data)
    water_usage_per_kg = 85.2
    chemical_usage = {
        "dye_chemicals": 2.5,
        "finishing_chemicals": 1.8
    }
    
    # İyileştirme aksiyonları (örnek data)
    improvement_actions = [
        {
            "title": "LED Aydınlatma Geçişi" if lang == "tr" else "LED Lighting Transition",
            "description": "Tüm fabrika aydınlatmasını LED'e çevirme" if lang == "tr" else "Convert all factory lighting to LED",
            "priority": "high",
            "status": "in_progress",
            "expected_reduction": 12,
            "investment": "₺150,000",
            "payback_months": 18
        },
        {
            "title": "Güneş Paneli Kurulumu" if lang == "tr" else "Solar Panel Installation",
            "description": "Çatıya 500kW güneş paneli sistemi" if lang == "tr" else "500kW solar panel system on roof",
            "priority": "high",
            "status": "pending",
            "expected_reduction": 35,
            "investment": "₺2,500,000",
            "payback_months": 48
        },
        {
            "title": "Su Geri Dönüşüm Sistemi" if lang == "tr" else "Water Recycling System",
            "description": "Boyahane atık suyunu arıtma ve tekrar kullanma" if lang == "tr" else "Treat and reuse dyehouse wastewater",
            "priority": "medium",
            "status": "completed",
            "expected_reduction": 8,
            "investment": "₺800,000",
            "payback_months": 36
        },
        {
            "title": "Çevre Dostu Boyar Madde" if lang == "tr" else "Eco-friendly Dyes",
            "description": "Düşük etkili doğal boyar maddelere geçiş" if lang == "tr" else "Transition to low-impact natural dyes",
            "priority": "low",
            "status": "in_progress",
            "expected_reduction": 5,
            "investment": "₺200,000",
            "payback_months": 24
        }
    ]
    
    # Sertifikasyon ilerlemesi (örnek data)
    certifications = {
        "iso14001": 85,
        "oeko_tex": 60,
        "gots_certification": 40,
        "carbon_neutral": 25
    }
    
    # Karbon yoğunluğu hesaplama
    total_production = len(styles) * 1000  # varsayılan üretim miktarı
    carbon_intensity = current_month_emissions / (total_production / 1000) if total_production > 0 else 0
    
    # Tedarikçi skorları (örnek data) 
    supplier_scores = [
        {"name": "ABC Tekstil", "score": 85, "category": "İplik", "location": "Bursa"},
        {"name": "XYZ Dokuma", "score": 78, "category": "Kumaş", "location": "İstanbul"},
        {"name": "DEF Kimya", "score": 62, "category": "Boyar Madde", "location": "İzmir"},
        {"name": "GHI Aksesuar", "score": 91, "category": "Düğme/Fermuar", "location": "Çorum"}
    ]
    
    response = templates.TemplateResponse("carbon_followup.html", {
        "request": request,
        "current_month_emissions": round(current_month_emissions, 2),
        "yearly_target": round(yearly_target, 2),
        "reduction_progress": round(reduction_progress, 1),
        "energy_mix": energy_mix,
        "water_usage_per_kg": water_usage_per_kg,
        "chemical_usage": chemical_usage,
        "improvement_actions": improvement_actions,
        "certifications": certifications,
        "carbon_intensity": round(carbon_intensity, 2),
        "supplier_scores": supplier_scores,
        "lang": lang,
        "t": get_all_texts(lang)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """API: İstatistikler"""
    collections = mango_dpp.get_collections(db)
    styles = mango_dpp.get_styles(db)
    nfts = mango_dpp.get_nfts(db)
    
    return {
        "collections": len(collections),
        "styles": len(styles),
        "samples": 0,
        "nfts": len(nfts),
        "total_carbon": sum([s.carbon_footprint or 0 for s in styles])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)