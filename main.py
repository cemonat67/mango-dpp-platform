from fastapi import FastAPI, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
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
        
        # NFT'yi sakla
        self.nfts[nft_id] = nft_data
        
        return nft_data
    
    def setup_ai_client(self):
        """AI client kurulumu"""
        try:
            # Keyring'den OpenAI API key'i al
            api_key = None
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
            print(f"AI görsel oluşturma hatası: {e}")
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

@app.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Ana dashboard"""
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
        "collections": collections[:5]
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/collections")
async def collections_page(request: Request, db: Session = Depends(get_db)):
    """Koleksiyonlar sayfası"""
    collections = mango_dpp.get_collections(db)
    response = templates.TemplateResponse("collections.html", {
        "request": request,
        "collections": collections
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

@app.get("/styles")
async def styles_page(request: Request, db: Session = Depends(get_db)):
    """Stiller sayfası"""
    styles = mango_dpp.get_styles(db)
    collections = mango_dpp.get_collections(db)
    
    response = templates.TemplateResponse("styles.html", {
        "request": request,
        "styles": styles,
        "collections": collections
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
async def generate_style_image(style_id: str):
    """Var olan stil için AI görsel oluştur"""
    if style_id not in mango_dpp.styles:
        return JSONResponse({"error": "Stil bulunamadı"}, status_code=404)
    
    if not mango_dpp.ai_enabled:
        return JSONResponse({"error": "AI görsel oluşturma devre dışı. OpenAI API key gerekli."}, status_code=400)
    
    style = mango_dpp.styles[style_id]
    
    try:
        image_path = await mango_dpp.generate_product_image(style)
        if image_path:
            style["image_url"] = image_path
            style["status"] = "görsel_oluşturuldu"
            mango_dpp.styles[style_id] = style
            
            return JSONResponse({
                "success": True,
                "image_url": image_path,
                "message": "Görsel başarıyla oluşturuldu"
            })
        else:
            return JSONResponse({"error": "Görsel oluşturulamadı"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"error": f"Görsel oluşturma hatası: {str(e)}"}, status_code=500)

@app.get("/passport/{nft_id}", response_class=HTMLResponse)
async def nft_passport(request: Request, nft_id: str):
    """NFT dijital pasaport görüntüle"""
    if nft_id not in mango_dpp.nfts:
        return templates.TemplateResponse("404.html", {"request": request})
    
    nft_data = mango_dpp.nfts[nft_id]
    return templates.TemplateResponse("passport.html", {
        "request": request,
        "nft": nft_data
    })

@app.post("/generate-nft")
async def generate_nft_passport(
    style_id: str = Form(...),
    certificates: str = Form(""),
    additional_info: str = Form("")
):
    """Stil için NFT pasaport oluştur"""
    if style_id not in mango_dpp.styles:
        return JSONResponse({"error": "Stil bulunamadı"}, status_code=404)
    
    style = mango_dpp.styles[style_id]
    collection = mango_dpp.collections.get(style["collection_id"], {})
    
    product_data = {
        "code": f"MNG-{style_id[:8]}",
        "name": style["name"],
        "collection": collection.get("name", ""),
        "materials": style["materials"],
        "production_location": style["production_location"],
        "carbon_footprint": style["carbon_footprint"],
        "certificates": [c.strip() for c in certificates.split(",") if c.strip()],
        "supplier": style["supplier"],
        "additional_info": additional_info
    }
    
    nft_data = mango_dpp.create_nft_passport(product_data)
    
    # Stili güncelle
    mango_dpp.styles[style_id]["nft_id"] = nft_data["id"]
    mango_dpp.styles[style_id]["status"] = "nft_oluşturuldu"
    
    return JSONResponse({
        "success": True,
        "nft_id": nft_data["id"],
        "qr_code": nft_data["qr_code"],
        "passport_url": nft_data["qr_url"]
    })

@app.get("/sustainability", response_class=HTMLResponse)
async def sustainability_page(request: Request):
    """Sürdürülebilirlik dashboard"""
    total_carbon = sum([style.get("carbon_footprint", 0) for style in mango_dpp.styles.values()])
    avg_carbon = total_carbon / len(mango_dpp.styles) if mango_dpp.styles else 0
    
    # En düşük karbon ayak izli stiller
    low_carbon_styles = sorted(
        mango_dpp.styles.values(),
        key=lambda x: x.get("carbon_footprint", 0)
    )[:5]
    
    # Karbon kategorilerine göre dağılım
    low_carbon_count = len([s for s in mango_dpp.styles.values() if s.get("carbon_footprint", 0) < 3])
    medium_carbon_count = len([s for s in mango_dpp.styles.values() if 3 <= s.get("carbon_footprint", 0) <= 5])
    high_carbon_count = len([s for s in mango_dpp.styles.values() if s.get("carbon_footprint", 0) > 5])
    
    # Malzeme analizi
    material_analysis = {}
    for style in mango_dpp.styles.values():
        for material in style.get("materials", []):
            if material not in material_analysis:
                material_analysis[material] = {"count": 0, "total_carbon": 0}
            material_analysis[material]["count"] += 1
            material_analysis[material]["total_carbon"] += style.get("carbon_footprint", 0)
    
    # Ortalama karbon hesapla
    for material in material_analysis:
        material_analysis[material]["avg_carbon"] = round(
            material_analysis[material]["total_carbon"] / material_analysis[material]["count"], 2
        )
    
    return templates.TemplateResponse("sustainability.html", {
        "request": request,
        "total_carbon": round(total_carbon, 2),
        "avg_carbon": round(avg_carbon, 2),
        "low_carbon_styles": low_carbon_styles,
        "total_styles": len(mango_dpp.styles),
        "low_carbon_count": low_carbon_count,
        "medium_carbon_count": medium_carbon_count,
        "high_carbon_count": high_carbon_count,
        "material_analysis": material_analysis
    })

@app.get("/sustainability/materials", response_class=HTMLResponse)
async def materials_analysis(request: Request):
    """Malzeme bazlı sürdürülebilirlik analizi"""
    material_stats = {}
    
    for style in mango_dpp.styles.values():
        for material in style.get("materials", []):
            if material not in material_stats:
                material_stats[material] = {
                    "styles": [],
                    "total_carbon": 0,
                    "avg_carbon": 0,
                    "usage_count": 0,
                    "sustainability_score": 0
                }
            
            material_stats[material]["styles"].append(style)
            material_stats[material]["total_carbon"] += style.get("carbon_footprint", 0)
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
    
    return templates.TemplateResponse("materials_analysis.html", {
        "request": request,
        "material_stats": material_stats,
        "best_materials": best_materials,
        "worst_materials": worst_materials
    })

@app.get("/sustainability/production", response_class=HTMLResponse)
async def production_analysis(request: Request):
    """Üretim lokasyonu bazlı analiz"""
    location_stats = {}
    
    for style in mango_dpp.styles.values():
        location = style.get("production_location", "Bilinmiyor")
        if location not in location_stats:
            location_stats[location] = {
                "styles": [],
                "total_carbon": 0,
                "avg_carbon": 0,
                "count": 0
            }
        
        location_stats[location]["styles"].append(style)
        location_stats[location]["total_carbon"] += style.get("carbon_footprint", 0)
        location_stats[location]["count"] += 1
    
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
    
    return templates.TemplateResponse("production_analysis.html", {
        "request": request,
        "location_stats": location_stats,
        "best_locations": best_locations
    })

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