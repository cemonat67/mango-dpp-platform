from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

app = FastAPI(title="Mango DPP - Digital Product Platform")

# Static files ve templates
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory database (gerçek uygulamada PostgreSQL kullanılacak)
collections_db = {}
styles_db = {}
samples_db = {}
suppliers_db = {}
nft_db = {}
carbon_db = {}

class MangoDPP:
    def __init__(self):
        self.collections = collections_db
        self.styles = styles_db
        self.samples = samples_db
        self.suppliers = suppliers_db
        self.nfts = nft_db
        self.carbon = carbon_db
        
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

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Ana dashboard"""
    stats = {
        "total_collections": len(mango_dpp.collections),
        "total_styles": len(mango_dpp.styles),
        "total_samples": len(mango_dpp.samples),
        "total_nfts": len(mango_dpp.nfts)
    }
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "stats": stats,
        "collections": list(mango_dpp.collections.values())[:5]
    })

@app.get("/collections", response_class=HTMLResponse)
async def collections_page(request: Request):
    """Koleksiyonlar sayfası"""
    return templates.TemplateResponse("collections.html", {
        "request": request,
        "collections": list(mango_dpp.collections.values())
    })

@app.post("/collections")
async def create_collection(
    name: str = Form(...),
    season: str = Form(...),
    year: int = Form(...),
    description: str = Form(...)
):
    """Yeni koleksiyon oluştur"""
    collection_id = str(uuid.uuid4())
    collection = {
        "id": collection_id,
        "name": name,
        "season": season,
        "year": year,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "styles": []
    }
    mango_dpp.collections[collection_id] = collection
    return JSONResponse({"success": True, "collection_id": collection_id})

@app.get("/styles", response_class=HTMLResponse)
async def styles_page(request: Request):
    """Stiller sayfası"""
    return templates.TemplateResponse("styles.html", {
        "request": request,
        "styles": list(mango_dpp.styles.values()),
        "collections": list(mango_dpp.collections.values())
    })

@app.post("/styles")
async def create_style(
    name: str = Form(...),
    collection_id: str = Form(...),
    category: str = Form(...),
    materials: str = Form(...),
    target_price: float = Form(...),
    production_location: str = Form(...),
    supplier: str = Form(...)
):
    """Yeni stil oluştur"""
    style_id = str(uuid.uuid4())
    materials_list = [m.strip() for m in materials.split(",")]
    
    # Karbon ayak izi hesapla
    carbon_footprint = mango_dpp.calculate_carbon_footprint(
        materials_list, production_location, "sea"
    )
    
    style = {
        "id": style_id,
        "name": name,
        "collection_id": collection_id,
        "category": category,
        "materials": materials_list,
        "target_price": target_price,
        "production_location": production_location,
        "supplier": supplier,
        "carbon_footprint": carbon_footprint,
        "created_at": datetime.now().isoformat(),
        "status": "tasarım"
    }
    
    mango_dpp.styles[style_id] = style
    
    # Koleksiyona stil ekle
    if collection_id in mango_dpp.collections:
        mango_dpp.collections[collection_id]["styles"].append(style_id)
    
    return JSONResponse({"success": True, "style_id": style_id})

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
    
    return templates.TemplateResponse("sustainability.html", {
        "request": request,
        "total_carbon": round(total_carbon, 2),
        "avg_carbon": round(avg_carbon, 2),
        "low_carbon_styles": low_carbon_styles,
        "total_styles": len(mango_dpp.styles)
    })

@app.get("/api/stats")
async def get_stats():
    """API: İstatistikler"""
    return {
        "collections": len(mango_dpp.collections),
        "styles": len(mango_dpp.styles),
        "samples": len(mango_dpp.samples),
        "nfts": len(mango_dpp.nfts),
        "total_carbon": sum([s.get("carbon_footprint", 0) for s in mango_dpp.styles.values()])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)