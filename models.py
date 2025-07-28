from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    season = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    styles = relationship("Style", back_populates="collection")

class Style(Base):
    __tablename__ = "styles"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    collection_id = Column(String, ForeignKey("collections.id"))
    category = Column(String, nullable=False)
    materials = Column(JSON)  # Store as JSON array
    target_price = Column(Float)
    production_location = Column(String)
    supplier = Column(String)
    carbon_footprint = Column(Float)
    status = Column(String, default="tasarım")
    image_url = Column(String)
    nft_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    collection = relationship("Collection", back_populates="styles")

class NFTPassport(Base):
    __tablename__ = "nft_passports"
    
    id = Column(String, primary_key=True)
    style_id = Column(String, ForeignKey("styles.id"))
    product_code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    collection_name = Column(String)
    materials = Column(JSON)
    production_location = Column(String)
    carbon_footprint = Column(Float)
    certificates = Column(JSON)
    supplier = Column(String)
    blockchain_hash = Column(String)
    qr_code_data = Column(Text)
    qr_url = Column(String)
    additional_info = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String)
    contact_info = Column(JSON)
    sustainability_score = Column(Float)
    certificates = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)