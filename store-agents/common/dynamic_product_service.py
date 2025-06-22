import os
import sys
import json
import asyncio
import logging
import aiohttp
from typing import Dict, List, Set, Optional, Tuple, Any
from fuzzywuzzy import fuzz, process
import re

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

class DynamicProductService:
    """Service for managing dynamic, location and industry-specific product databases"""
    
    def __init__(self):
        self.cache_dir = os.path.join(project_root, 'data', 'product_databases')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache for loaded product databases
        self._product_cache: Dict[str, Dict] = {}
        
    def get_cache_key(self, country: str, industry: str) -> str:
        """Generate cache key for country-industry combination"""
        return f"{country.lower()}_{industry.lower()}".replace(' ', '_')
    
    def get_cache_file_path(self, cache_key: str) -> str:
        """Get file path for cached product database"""
        return os.path.join(self.cache_dir, f"{cache_key}_products.json")
    
    async def get_product_database(self, country: str, industry: str) -> Dict[str, Any]:
        """Get product database for specific country and industry"""
        cache_key = self.get_cache_key(country, industry)
        
        # Check in-memory cache first
        if cache_key in self._product_cache:
            logger.info(f"🔥 Using cached product database for {country}-{industry}")
            return self._product_cache[cache_key]
        
        # Check file cache
        cache_file = self.get_cache_file_path(cache_key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    product_db = json.load(f)
                    self._product_cache[cache_key] = product_db
                    logger.info(f"📁 Loaded product database from cache for {country}-{industry}")
                    return product_db
            except Exception as e:
                logger.warning(f"Failed to load cached database: {e}")
        
        # Scrape new data if not cached
        logger.info(f"🌐 Scraping new product database for {country}-{industry}")
        product_db = await self._scrape_product_database(country, industry)
        
        # Cache the results
        await self._cache_product_database(cache_key, product_db)
        
        return product_db
    
    async def _scrape_product_database(self, country: str, industry: str) -> Dict[str, Any]:
        """Scrape product data for specific country and industry"""
        
        try:
            # Multi-source scraping strategy
            scraped_data = {
                'brands': set(),
                'products': [],
                'categories': {},
                'brand_variations': {},
                'country': country,
                'industry': industry,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
            # Source 1: E-commerce sites
            ecommerce_data = await self._scrape_ecommerce_sites(country, industry)
            scraped_data['brands'].update(ecommerce_data.get('brands', []))
            scraped_data['products'].extend(ecommerce_data.get('products', []))
            
            # Source 2: Supermarket chains
            supermarket_data = await self._scrape_supermarket_chains(country, industry)
            scraped_data['brands'].update(supermarket_data.get('brands', []))
            scraped_data['products'].extend(supermarket_data.get('products', []))
            
            # Source 3: Industry-specific databases
            industry_data = await self._scrape_industry_databases(country, industry)
            scraped_data['brands'].update(industry_data.get('brands', []))
            scraped_data['products'].extend(industry_data.get('products', []))
            
            # Process and clean the data
            scraped_data = await self._process_scraped_data(scraped_data)
            
            logger.info(f"✅ Scraped {len(scraped_data['brands'])} brands and {len(scraped_data['products'])} products")
            
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping product database: {e}")
            # Return fallback data
            return await self._get_fallback_database(country, industry)
    
    async def _scrape_ecommerce_sites(self, country: str, industry: str) -> Dict[str, List]:
        """Scrape major e-commerce sites for product data"""
        
        scraped_data = {'brands': [], 'products': []}
        
        try:
            # Country-specific e-commerce sites mapping
            ecommerce_sites = self._get_ecommerce_sites(country)
            
            async with aiohttp.ClientSession() as session:
                for site_config in ecommerce_sites:
                    try:
                        site_data = await self._scrape_single_ecommerce_site(
                            session, site_config, industry
                        )
                        scraped_data['brands'].extend(site_data.get('brands', []))
                        scraped_data['products'].extend(site_data.get('products', []))
                        
                    except Exception as e:
                        logger.warning(f"Failed to scrape {site_config.get('name', 'site')}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error scraping e-commerce sites: {e}")
        
        return scraped_data
    
    async def _scrape_supermarket_chains(self, country: str, industry: str) -> Dict[str, List]:
        """Scrape major supermarket chains for product data"""
        
        scraped_data = {'brands': [], 'products': []}
        
        try:
            # Country-specific supermarket chains
            supermarket_sites = self._get_supermarket_sites(country)
            
            async with aiohttp.ClientSession() as session:
                for site_config in supermarket_sites:
                    try:
                        site_data = await self._scrape_single_supermarket_site(
                            session, site_config, industry
                        )
                        scraped_data['brands'].extend(site_data.get('brands', []))
                        scraped_data['products'].extend(site_data.get('products', []))
                        
                    except Exception as e:
                        logger.warning(f"Failed to scrape {site_config.get('name', 'supermarket')}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error scraping supermarket sites: {e}")
        
        return scraped_data
    
    async def _scrape_industry_databases(self, country: str, industry: str) -> Dict[str, List]:
        """Scrape industry-specific databases and APIs"""
        
        scraped_data = {'brands': [], 'products': []}
        
        try:
            # Industry-specific data sources
            if industry.lower() in ['retail', 'grocery', 'supermarket']:
                scraped_data = await self._scrape_retail_databases(country)
            elif industry.lower() in ['pharmacy', 'healthcare']:
                scraped_data = await self._scrape_pharmacy_databases(country)
            elif industry.lower() in ['electronics', 'technology']:
                scraped_data = await self._scrape_electronics_databases(country)
            
        except Exception as e:
            logger.error(f"Error scraping industry databases: {e}")
        
        return scraped_data
    
    def _get_ecommerce_sites(self, country: str) -> List[Dict]:
        """Get e-commerce sites for specific country"""
        
        # Country-specific e-commerce mapping
        ecommerce_mapping = {
            'zimbabwe': [
                {'name': 'Zimall', 'url': 'https://zimall.co.zw', 'selectors': {'products': '.product-item', 'brand': '.brand'}},
                {'name': 'Classifieds', 'url': 'https://classifieds.co.zw', 'selectors': {'products': '.ad-item'}},
            ],
            'south africa': [
                {'name': 'Takealot', 'url': 'https://takealot.com', 'selectors': {'products': '.product-item'}},
                {'name': 'Game', 'url': 'https://game.co.za', 'selectors': {'products': '.product-tile'}},
                {'name': 'Checkers', 'url': 'https://checkers.co.za', 'selectors': {'products': '.product-item'}},
            ],
            'kenya': [
                {'name': 'Jumia', 'url': 'https://jumia.co.ke', 'selectors': {'products': '.product-item'}},
                {'name': 'Kilimall', 'url': 'https://kilimall.co.ke', 'selectors': {'products': '.product'}},
            ],
            'nigeria': [
                {'name': 'Jumia', 'url': 'https://jumia.com.ng', 'selectors': {'products': '.product-item'}},
                {'name': 'Konga', 'url': 'https://konga.com', 'selectors': {'products': '.product-item'}},
            ],
            'ghana': [
                {'name': 'Jumia', 'url': 'https://jumia.com.gh', 'selectors': {'products': '.product-item'}},
                {'name': 'Tonaton', 'url': 'https://tonaton.com', 'selectors': {'products': '.listing-item'}},
            ],
            'united states': [
                {'name': 'Amazon', 'url': 'https://amazon.com', 'selectors': {'products': '[data-component-type="s-search-result"]'}},
                {'name': 'Walmart', 'url': 'https://walmart.com', 'selectors': {'products': '.product-item'}},
            ],
            'united kingdom': [
                {'name': 'Tesco', 'url': 'https://tesco.com', 'selectors': {'products': '.product-item'}},
                {'name': 'ASDA', 'url': 'https://asda.com', 'selectors': {'products': '.product-item'}},
            ]
        }
        
        return ecommerce_mapping.get(country.lower(), [])
    
    def _get_supermarket_sites(self, country: str) -> List[Dict]:
        """Get supermarket sites for specific country"""
        
        supermarket_mapping = {
            'zimbabwe': [
                {'name': 'OK Zimbabwe', 'url': 'https://ok.co.zw', 'selectors': {'products': '.product'}},
                {'name': 'SPAR Zimbabwe', 'url': 'https://spar.co.zw', 'selectors': {'products': '.product-item'}},
            ],
            'south africa': [
                {'name': 'Pick n Pay', 'url': 'https://picknpay.co.za', 'selectors': {'products': '.product-tile'}},
                {'name': 'Woolworths', 'url': 'https://woolworths.co.za', 'selectors': {'products': '.product-item'}},
                {'name': 'Shoprite', 'url': 'https://shoprite.co.za', 'selectors': {'products': '.product'}},
            ],
            'kenya': [
                {'name': 'Carrefour Kenya', 'url': 'https://carrefour.ke', 'selectors': {'products': '.product-item'}},
                {'name': 'Naivas', 'url': 'https://naivas.online', 'selectors': {'products': '.product'}},
            ]
        }
        
        return supermarket_mapping.get(country.lower(), [])
    
    async def _scrape_single_ecommerce_site(self, session: aiohttp.ClientSession, 
                                          site_config: Dict, industry: str) -> Dict[str, List]:
        """Scrape a single e-commerce site"""
        
        # Implementation would depend on specific site structure
        # For now, return mock data structure
        return {
            'brands': [],
            'products': []
        }
    
    async def _scrape_single_supermarket_site(self, session: aiohttp.ClientSession,
                                            site_config: Dict, industry: str) -> Dict[str, List]:
        """Scrape a single supermarket site"""
        
        # Implementation would depend on specific site structure
        # For now, return mock data structure
        return {
            'brands': [],
            'products': []
        }
    
    async def _scrape_retail_databases(self, country: str) -> Dict[str, List]:
        """Scrape retail-specific databases"""
        return {'brands': [], 'products': []}
    
    async def _scrape_pharmacy_databases(self, country: str) -> Dict[str, List]:
        """Scrape pharmacy-specific databases"""
        return {'brands': [], 'products': []}
    
    async def _scrape_electronics_databases(self, country: str) -> Dict[str, List]:
        """Scrape electronics-specific databases"""
        return {'brands': [], 'products': []}
    
    async def _process_scraped_data(self, scraped_data: Dict) -> Dict[str, Any]:
        """Process and clean scraped data"""
        
        # Convert sets to lists for JSON serialization
        scraped_data['brands'] = list(scraped_data['brands'])
        
        # Remove duplicates and clean data
        scraped_data['brands'] = list(set([brand.lower().strip() for brand in scraped_data['brands'] if brand]))
        
        # Generate brand variations for better matching
        scraped_data['brand_variations'] = self._generate_brand_variations(scraped_data['brands'])
        
        # Categorize products
        scraped_data['categories'] = self._categorize_products(scraped_data['products'])
        
        return scraped_data
    
    def _generate_brand_variations(self, brands: List[str]) -> Dict[str, List[str]]:
        """Generate brand variations for OCR error handling"""
        
        variations = {}
        
        for brand in brands:
            brand_variations = []
            
            # Common variations
            if ' ' in brand:
                # With and without spaces
                brand_variations.append(brand.replace(' ', ''))
                brand_variations.append(brand.replace(' ', '-'))
            
            # Common OCR errors
            brand_variations.extend(self._generate_ocr_variations(brand))
            
            if brand_variations:
                variations[brand] = brand_variations
        
        return variations
    
    def _generate_ocr_variations(self, brand: str) -> List[str]:
        """Generate common OCR error variations"""
        
        variations = []
        
        # Common OCR character substitutions
        ocr_substitutions = {
            'o': '0', '0': 'o',
            'i': '1', '1': 'i', 'l': '1',
            's': '5', '5': 's',
            'b': '8', '8': 'b',
            'g': '9', '9': 'g',
        }
        
        # Generate variations with single character substitutions
        for i, char in enumerate(brand.lower()):
            if char in ocr_substitutions:
                variation = brand[:i] + ocr_substitutions[char] + brand[i+1:]
                variations.append(variation)
        
        return variations
    
    def _categorize_products(self, products: List[Dict]) -> Dict[str, List]:
        """Categorize products by type"""
        
        categories = {
            'beverages': [],
            'food': [],
            'household': [],
            'personal_care': [],
            'electronics': [],
            'clothing': [],
            'other': []
        }
        
        # Categorization logic would be implemented here
        # For now, return empty categories
        
        return categories
    
    async def _get_fallback_database(self, country: str, industry: str) -> Dict[str, Any]:
        """Get fallback database when scraping fails"""
        
        # Basic fallback with common global brands
        fallback_data = {
            'brands': [
                'coca cola', 'pepsi', 'nestle', 'unilever', 'procter & gamble',
                'johnson & johnson', 'kraft', 'heinz', 'mars', 'kelloggs'
            ],
            'products': [],
            'categories': {},
            'brand_variations': {},
            'country': country,
            'industry': industry,
            'is_fallback': True,
            'scraped_at': asyncio.get_event_loop().time()
        }
        
        # Add country-specific fallbacks
        if country.lower() == 'zimbabwe':
            fallback_data['brands'].extend([
                'delta', 'lobels', 'blue ribbon', 'mazoe', 'tanganda', 'cairns',
                'dairibord', 'tregers', 'bakers inn', 'proton', 'willowton'
            ])
        elif country.lower() == 'south africa':
            fallback_data['brands'].extend([
                'pick n pay', 'woolworths', 'shoprite', 'checkers', 'spar',
                'koo', 'all joy', 'iwisa', 'jungle oats', 'black cat'
            ])
        
        fallback_data['brand_variations'] = self._generate_brand_variations(fallback_data['brands'])
        
        return fallback_data
    
    async def _cache_product_database(self, cache_key: str, product_db: Dict):
        """Cache product database to file and memory"""
        
        try:
            # Cache to file
            cache_file = self.get_cache_file_path(cache_key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(product_db, f, indent=2, ensure_ascii=False)
            
            # Cache to memory
            self._product_cache[cache_key] = product_db
            
            logger.info(f"💾 Cached product database for {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to cache product database: {e}")
    
    def fuzzy_match_brands(self, detected_text: str, brands: List[str], 
                          brand_variations: Dict[str, List[str]], 
                          threshold: int = 70) -> List[Tuple[str, int, str]]:
        """Perform fuzzy matching on detected text against known brands"""
        
        matches = []
        detected_text_lower = detected_text.lower()
        
        # Direct fuzzy matching against brands
        for brand in brands:
            # Exact match
            if brand in detected_text_lower:
                matches.append((brand, 100, 'exact'))
                continue
            
            # Fuzzy match
            ratio = fuzz.partial_ratio(brand, detected_text_lower)
            if ratio >= threshold:
                matches.append((brand, ratio, 'fuzzy'))
            
            # Check variations
            if brand in brand_variations:
                for variation in brand_variations[brand]:
                    if variation.lower() in detected_text_lower:
                        matches.append((brand, 95, 'variation'))
                        break
                    
                    var_ratio = fuzz.partial_ratio(variation, detected_text_lower)
                    if var_ratio >= threshold:
                        matches.append((brand, var_ratio, 'variation_fuzzy'))
                        break
        
        # Sort by confidence score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Remove duplicates (keep highest scoring)
        seen_brands = set()
        unique_matches = []
        for match in matches:
            if match[0] not in seen_brands:
                unique_matches.append(match)
                seen_brands.add(match[0])
        
        return unique_matches[:5]  # Return top 5 matches
    
    async def refresh_product_database(self, country: str, industry: str) -> bool:
        """Force refresh of product database"""
        
        try:
            cache_key = self.get_cache_key(country, industry)
            
            # Remove from caches
            if cache_key in self._product_cache:
                del self._product_cache[cache_key]
            
            cache_file = self.get_cache_file_path(cache_key)
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            # Re-scrape
            await self.get_product_database(country, industry)
            
            logger.info(f"🔄 Refreshed product database for {country}-{industry}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh product database: {e}")
            return False


# Global instance
dynamic_product_service = DynamicProductService()
