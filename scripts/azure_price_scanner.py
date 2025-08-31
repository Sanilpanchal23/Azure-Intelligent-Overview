#!/usr/bin/env python3
"""
Azure Price Intelligence Scanner - OPTIMIZED
-----------------------------------
The perfect Azure VM price scanner that actually works with the current API.
Collects all data needed for your dashboard with proper filtering and error handling.
"""

import argparse
import json
import re
import sys
import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import requests

# Try to import the VM specs lookup
try:
    from vm_specs_lookup import get_vm_specs
    VM_SPECS_AVAILABLE = True
except ImportError:
    VM_SPECS_AVAILABLE = False
    print("Note: vm_specs_lookup.py not found. Using basic parsing only.")

# Constants
AZURE_API_URL = "https://prices.azure.com/api/retail/prices"
DEFAULT_OUTPUT = "../dashboard/data/azure_prices.json"
USER_AGENT = "Azure-Price-Intelligence-Dashboard/1.0"

# Regex patterns
VCPU_PATTERN = re.compile(r'(\d+)\s*vCPU', re.IGNORECASE)
RAM_PATTERN = re.compile(r'(\d+)\s*GB', re.IGNORECASE)
SERIES_PATTERN = re.compile(r'([A-Za-z]+)\d*[a-z]*\s*v?(\d+)', re.IGNORECASE)

class AzurePriceScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    def build_query_filter(self, os_filter: str) -> str:
        """Build filter - only service name, we handle consumption detection ourselves"""
        base_filter = "serviceName eq 'Virtual Machines'"
        if os_filter == "linux":
            return f"{base_filter} and contains(productName, 'Linux')"
        elif os_filter == "windows":
            return f"{base_filter} and contains(productName, 'Windows')"
        return base_filter
    
    def is_consumption_pricing(self, item: Dict[str, Any]) -> bool:
        """
        Smart consumption detection since Azure API is unreliable:
        - Must be hourly pricing (unitOfMeasure contains 'Hour')
        - Must NOT be reservation, SQL, database, storage, etc.
        - Must have reasonable price (< $1000/hr sanity check)
        """
        unit = (item.get("unitOfMeasure") or "").lower()
        meter_name = (item.get("meterName") or "").lower()
        product_name = (item.get("productName") or "").lower()
        sku_name = (item.get("skuName") or "").lower()
        
        # Must be hourly pricing
        if "hour" not in unit:
            return False
        
        # Exclude non-VM items
        exclusion_terms = [
            "reservation", "sql", "database", "storage", "bandwidth", 
            "snapshot", "backup", "oracle", "premium ssd", "managed disk"
        ]
        
        combined_text = f"{meter_name} {product_name} {sku_name}".lower()
        for term in exclusion_terms:
            if term in combined_text:
                return False
        
        # Price sanity check
        price = item.get("retailPrice") or item.get("unitPrice") or 0
        try:
            price_float = float(price)
            if price_float > 1000:  # No VM should cost > $1000/hr
                return False
        except (ValueError, TypeError):
            pass
            
        return True
    
    def parse_vm_specs(self, product_name: str, sku_name: str, vm_name: str) -> Dict[str, Any]:
        """
        Enhanced VM specs parsing using lookup table when available
        """
        specs = {"vcpus": None, "memoryGB": None}
        
        # First try the lookup table if available
        if VM_SPECS_AVAILABLE:
            lookup_specs = get_vm_specs(vm_name)
            if lookup_specs["vcpus"] is not None:
                specs["vcpus"] = lookup_specs["vcpus"]
            if lookup_specs["memoryGB"] is not None:
                specs["memoryGB"] = lookup_specs["memoryGB"]
        
        # If lookup didn't find everything, try regex parsing as fallback
        if not specs["vcpus"] or not specs["memoryGB"]:
            search_text = f"{product_name or ''} {sku_name or ''}".lower()
            
            if not specs["vcpus"]:
                vcpu_match = VCPU_PATTERN.search(search_text)
                if vcpu_match:
                    try:
                        specs["vcpus"] = int(vcpu_match.group(1))
                    except (ValueError, TypeError):
                        pass
            
            if not specs["memoryGB"]:
                ram_match = RAM_PATTERN.search(search_text)
                if ram_match:
                    try:
                        specs["memoryGB"] = int(ram_match.group(1))
                    except (ValueError, TypeError):
                        pass
        
        return specs
    
    def determine_os_type(self, product_name: str, sku_name: str) -> str:
        combined_text = f"{product_name or ''} {sku_name or ''}".lower()
        if "windows" in combined_text:
            return "Windows"
        elif "linux" in combined_text:
            return "Linux"
        
        # Additional detection for common Linux patterns
        linux_indicators = ["ubuntu", "red hat", "rhel", "suse", "debian", "centos"]
        for indicator in linux_indicators:
            if indicator in combined_text:
                return "Linux"
                
        return "Unknown"
    
    def is_spot_instance(self, sku_name: str, product_name: str) -> bool:
        combined_text = f"{sku_name or ''} {product_name or ''}".lower()
        spot_indicators = ["spot", "low priority", "low-priority"]
        return any(indicator in combined_text for indicator in spot_indicators)
    
    def extract_series_info(self, sku_name: str, arm_sku_name: str) -> Dict[str, Optional[str]]:
        source_text = arm_sku_name or sku_name or ""
        series_match = SERIES_PATTERN.search(source_text)
        if series_match:
            family = series_match.group(1)
            generation = series_match.group(2)
            series = f"{family}v{generation}"
        else:
            family_match = re.match(r'([A-Za-z]+)', source_text.replace("Standard_", ""))
            family = family_match.group(1) if family_match else None
            series = family
        
        return {"series": series, "family": family, "size": sku_name or arm_sku_name}
    
    def fetch_vm_prices(self, os_filter: str = "both", include_spot: bool = False, 
                       regions: Optional[List[str]] = None, max_pages: int = 0, 
                       timeout: int = 30) -> List[Dict[str, Any]]:
        all_items = []
        next_url = None
        page_count = 0
        
        # Generate random page limit between 75-250 if max_pages is 0
        if max_pages == 0:
            max_pages = random.randint(10, 100)
            print(f"Random page limit set to: {max_pages} pages")
        
        query_filter = self.build_query_filter(os_filter)
        params = {"$filter": query_filter, "currencyCode": "USD"}
        
        print(f"Starting data collection with filter: {query_filter}")
        print(f"Page limit: {max_pages} pages")
        if VM_SPECS_AVAILABLE:
            print("Using enhanced VM specs lookup table")
        else:
            print("Using basic VM specs parsing (vm_specs_lookup.py not found)")
        
        while True:
            page_count += 1
            if max_pages > 0 and page_count > max_pages:
                print(f"Reached maximum page limit ({max_pages})")
                break
            
            url = next_url if next_url else AZURE_API_URL
            params = {} if next_url else params
            
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                items = data.get("Items", [])
                print(f"Page {page_count}: Processing {len(items)} items")
                
                for item in items:
                    if self._should_include_item(item, include_spot, regions):
                        processed_item = self._process_item(item)
                        if processed_item:
                            all_items.append(processed_item)
                
                next_url = data.get("NextPageLink")
                if not next_url:
                    print("No more pages available")
                    break
                
                time.sleep(0.3)  # Respectful delay
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page_count}: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                break
        
        print(f"Data collection complete. Total items: {len(all_items)}")
        return all_items
    
    def _should_include_item(self, item: Dict[str, Any], include_spot: bool, 
                           regions: Optional[List[str]]) -> bool:
        # Check if it's a VM
        if item.get("serviceName") != "Virtual Machines":
            return False
        
        # Use our smart consumption detection
        if not self.is_consumption_pricing(item):
            return False
        
        # Check spot instances
        sku_name = item.get("skuName", "")
        product_name = item.get("productName", "")
        if not include_spot and self.is_spot_instance(sku_name, product_name):
            return False
        
        # Check region filter
        if regions:
            item_region = item.get("armRegionName") or item.get("location", "")
            if not item_region:
                return False
            if item_region.lower() not in [r.lower() for r in regions]:
                return False
        
        return True
    
    def _process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sku_name = item.get("skuName", "")
            product_name = item.get("productName", "")
            arm_sku_name = item.get("armSkuName", "")
            
            series_info = self.extract_series_info(sku_name, arm_sku_name)
            vm_name = series_info["size"] or sku_name or arm_sku_name
            
            # Use enhanced parsing with VM name
            specs = self.parse_vm_specs(product_name, sku_name, vm_name)
            os_type = self.determine_os_type(product_name, sku_name)
            is_spot = self.is_spot_instance(sku_name, product_name)
            
            price = item.get("retailPrice") or item.get("unitPrice") or 0.0
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0.0
            
            # Final price sanity check
            if price > 1000:  # Skip extremely high prices
                return None
            
            processed = {
                "name": vm_name,
                "skuName": sku_name,
                "productName": product_name,
                "armSkuName": arm_sku_name,
                "series": series_info["series"],
                "family": series_info["family"],
                "size": series_info["size"],
                "os": os_type,
                "isSpot": is_spot,
                "vcpus": specs["vcpus"],
                "memoryGB": specs["memoryGB"],
                "pricePerHour": price,
                "currencyCode": item.get("currencyCode", "USD"),
                "unitOfMeasure": item.get("unitOfMeasure", "1 Hour"),
                "region": item.get("armRegionName") or item.get("location", ""),
                "meterId": item.get("meterId"),
                "skuId": item.get("skuId"),
                "productId": item.get("productId"),
                "effectiveStartDate": item.get("effectiveStartDate"),
                "offerTermCode": item.get("offerTermCode"),
                "serviceFamily": item.get("serviceFamily"),
                "meterName": item.get("meterName"),
                "priceType": item.get("priceType"),
            }
            
            return processed
            
        except Exception as e:
            print(f"Error processing item: {e}")
            return None
    
    def generate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not items:
            return {
                "count": 0,
                "regionsCount": 0,
                "regions": [],
                "familiesCount": 0,
                "families": [],
                "osTypes": [],
                "spotCount": 0,
                "avgPricePerHour": 0.0,
                "minPricePerHour": 0.0,
                "maxPricePerHour": 0.0,
            }
        
        prices = [item.get("pricePerHour", 0) for item in items if item.get("pricePerHour") is not None]
        regions = sorted(set(item.get("region", "") for item in items if item.get("region")))
        families = sorted(set(item.get("family", "") for item in items if item.get("family")))
        os_types = sorted(set(item.get("os", "") for item in items if item.get("os")))
        
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        spot_count = sum(1 for item in items if item.get("isSpot"))
        
        return {
            "count": len(items),
            "regionsCount": len(regions),
            "regions": regions,
            "familiesCount": len(families),
            "families": families,
            "osTypes": os_types,
            "spotCount": spot_count,
            "avgPricePerHour": round(avg_price, 6),
            "minPricePerHour": round(min_price, 6),
            "maxPricePerHour": round(max_price, 6),
        }
    
    def save_to_json(self, items: List[Dict[str, Any]], filename: str) -> None:
        metadata = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": AZURE_API_URL,
            "itemCount": len(items),
            "summary": self.generate_summary(items)
        }
        
        output = {"metadata": metadata, "items": items}
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Azure VM Price Scanner - OPTIMIZED")
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help="Output JSON file")
    parser.add_argument("--os", choices=["linux", "windows", "both"], default="both", help="OS filter")
    parser.add_argument("--include-spot", action="store_true", help="Include Spot instances")
    parser.add_argument("--regions", type=str, default="", help="Comma-separated list of regions")
    parser.add_argument("--max-pages", type=int, default=0, help="Maximum pages to fetch (0 = random 75-250)")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    
    args = parser.parse_args()
    
    regions_list = [r.strip() for r in args.regions.split(",") if r.strip()] if args.regions else None
    
    scanner = AzurePriceScanner()
    
    print("Azure VM Price Scanner starting...")
    start_time = time.time()
    
    try:
        items = scanner.fetch_vm_prices(
            os_filter=args.os,
            include_spot=args.include_spot,
            regions=regions_list,
            max_pages=args.max_pages,
            timeout=args.timeout
        )
        
        scanner.save_to_json(items, args.out)
        
        duration = time.time() - start_time
        summary = scanner.generate_summary(items)
        
        print("\n=== COLLECTION SUMMARY ===")
        print(f"Total VMs: {summary['count']}")
        if summary['count'] > 0:
            print(f"Regions: {summary['regionsCount']}")
            print(f"Families: {summary['familiesCount']}")
            print(f"Spot Instances: {summary['spotCount']}")
            print(f"Avg Price: ${summary['avgPricePerHour']:.6f}/hr")
            print(f"Price Range: ${summary['minPricePerHour']:.6f} - ${summary['maxPricePerHour']:.6f}/hr")
        print(f"Duration: {duration:.2f} seconds")
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()