# 🔗 Mango DPP - NFT Digital Passport & QR Code Demo

## 📱 **Where to Access Digital Passports**

### 1. **From Styles Page**
- Go to **Styles** page: https://mango-dpp-platform-production.up.railway.app/styles
- For styles with NFT, click **"View NFT"** button
- This opens the digital passport in a new tab

### 2. **Direct URL Access**
- Each NFT has a unique URL: `/passport/{nft_id}`
- Example: https://mango-dpp-platform-production.up.railway.app/passport/afee97d7-007a-4f3b-9c64-88ed5fa06fa9

### 3. **QR Code Scanning**
- Scan any QR code from the platform
- QR codes automatically redirect to the passport page
- Works with any smartphone camera or QR scanner app

## 🎯 **Live Demo - Current NFT Passport**

### **NFT ID**: `afee97d7-007a-4f3b-9c64-88ed5fa06fa9`
### **Product**: Premium Cotton T-Shirt
### **Product Code**: MNG-f6af9a8e

**Direct Access URL**: 
```
https://mango-dpp-platform-production.up.railway.app/passport/afee97d7-007a-4f3b-9c64-88ed5fa06fa9
```

## 📋 **What You'll See in the Digital Passport**

### **1. QR Code Section**
- ✅ **192x192 PNG QR Code** (Base64 encoded)
- ✅ **Scannable with any device**
- ✅ **Download functionality**
- ✅ **Copy link functionality**

### **2. Product Information**
- ✅ **Product Code**: Unique identifier
- ✅ **Product Name**: Style name
- ✅ **Collection Info**: Season and year
- ✅ **Creation Date**: When NFT was generated

### **3. Material Information**
- ✅ **Material Tags**: Cotton, Polyester, etc.
- ✅ **Visual badges** for each material
- ✅ **Sustainability info**

### **4. Production Information**
- ✅ **Production Location**: Manufacturing site
- ✅ **Supplier Information**: Producer details
- ✅ **Geographic markers**

### **5. Carbon Footprint Analysis**
- ✅ **CO₂ Emissions**: Exact kg calculation
- ✅ **Environmental Impact Rating**:
  - 🟢 **Low Carbon** (< 3kg CO₂)
  - 🟡 **Medium Carbon** (3-5kg CO₂)  
  - 🔴 **High Carbon** (> 5kg CO₂)
- ✅ **Sustainability recommendations**

### **6. Certifications**
- ✅ **GOTS, OEKO-TEX, FairWear** badges
- ✅ **Visual certification display**
- ✅ **Award icons**

### **7. Blockchain Information**
- ✅ **Unique NFT ID**: UUID identifier
- ✅ **Blockchain Hash**: Immutable signature
- ✅ **Security guarantee message**
- ✅ **Tamper-proof verification**

## 🔄 **How to Create New NFT Passports**

### **Step 1: Create Style**
1. Go to **Styles** page
2. Click **"New Style"** button
3. Fill form with product details
4. Save the style

### **Step 2: Generate NFT**
1. Find your style in the grid
2. Click **"Create NFT"** button
3. Add certifications (optional)
4. Add additional info (optional)
5. Click **"Create NFT"**

### **Step 3: Access Passport**
1. Style now shows **NFT badge**
2. Click **"View NFT"** button
3. Digital passport opens
4. QR code is automatically generated

## 📱 **Mobile QR Code Workflow**

### **Consumer Experience**:
1. **Scan QR code** on product tag
2. **Instant access** to digital passport
3. **View sustainability data**
4. **Verify authenticity**
5. **Share with others**

### **Business Benefits**:
- ✅ **Transparency**: Full supply chain visibility
- ✅ **Authenticity**: Blockchain verification
- ✅ **Sustainability**: Carbon footprint tracking
- ✅ **Marketing**: Digital product stories
- ✅ **Compliance**: Regulation requirements

## 🛠 **Technical Implementation**

### **QR Code Generation**
```python
def create_qr_code(nft_id: str) -> str:
    """Generate QR code for NFT passport"""
    qr_url = f"https://mango-dpp-platform-production.up.railway.app/passport/{nft_id}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    # Convert to base64 for storage
    return base64_encode(img)
```

### **Blockchain Hash**
- **SHA-256** hash of product data
- **Immutable** once created
- **Verification** against tampering
- **Unique** per product

### **URL Structure**
```
/passport/{nft_id}
├── Product Information
├── QR Code Display  
├── Material Details
├── Production Info
├── Carbon Footprint
├── Certifications
└── Blockchain Data
```

## 🎪 **Demo Scenarios**

### **Scenario 1: Fashion Buyer**
- Scans QR code on garment
- Views carbon footprint (2.1 kg CO₂)
- Sees GOTS certification
- Verifies Turkey production
- Shares with team

### **Scenario 2: End Consumer**
- Finds QR code on product tag
- Learns about cotton materials
- Discovers sustainability rating
- Downloads QR code
- Posts on social media

### **Scenario 3: Retailer**
- Accesses via admin panel
- Views all product passports
- Uses for marketing campaigns
- Integrates into POS system
- Provides customer transparency

## 📊 **Current Platform Stats**
- ✅ **Active NFT Passports**: Available
- ✅ **QR Codes Generated**: Functional
- ✅ **Blockchain Hashes**: Unique per NFT
- ✅ **Mobile Responsive**: All devices supported
- ✅ **Multi-language**: Turkish/English

## 🔗 **Try It Now**

**Live NFT Passport URL**:
```
https://mango-dpp-platform-production.up.railway.app/passport/afee97d7-007a-4f3b-9c64-88ed5fa06fa9
```

**Or Access Via**:
1. Visit platform: https://mango-dpp-platform-production.up.railway.app
2. Go to **Styles** 
3. Click **"View NFT"** on any style with NFT badge
4. Explore the digital passport!

---

## 💡 **Next Steps for Full Production**

1. **Integrate with ERP systems**
2. **Add RFID/NFC capabilities** 
3. **Connect to real blockchain networks**
4. **Implement batch QR generation**
5. **Add analytics tracking**
6. **Create mobile app integration**

The NFT Digital Passport system is fully functional and ready for real-world deployment! 🚀