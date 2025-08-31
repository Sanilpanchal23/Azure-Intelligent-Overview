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
import os  # Added for reliable path handling
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
DEFAULT_OUTPUT_RELATIVE = "../dashboard/data/azure_prices.json"
USER_AGENT = "Azure-Price-Intelligence-Dashboard/1.0"

# Regex patterns
VCPU_PATTERN = re.compile(r'(\d+)\s*vCPU', re.IGNORECASE)
RAM_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*GB', re.IGNORECASE)
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
        Smart consumption detection since Azure API is unreliable.
        """
        unit = (item.get("unitOfMeasure") or "").lower()
        if "hour" not in unit:
            return False
        
        exclusion_terms = [
            "reservation", "sql", "database", "storage", "bandwidth", 
            "snapshot", "backup", "oracle", "premium ssd", "managed disk"
        ]
        
        combined_text = f"{item.get('meterName', '')} {item.get('productName', '')} {item.get('skuName', '')}".lower()
        if any(term in combined_text for term in exclusion_terms):
            return False
        
        try:
            price = float(item.get("retailPrice") or item.get("unitPrice") or 0)
            if price > 1000:
                return False
        except (ValueError, TypeError):
            pass
            
        return True
    
    def parse_vm_specs(self, product_name: str, sku_name: str, vm_name: str) -> Dict[str, Any]:
        """Enhanced VM specs parsing using lookup table when available"""
        specs = {"vcpus": None, "memoryGB": None}
        
        if VM_SPECS_AVAILABLE:
            lookup_specs = get_vm_specs(vm_name)
            if lookup_specs:
                specs.update(lookup_specs)

        if not specs.get("vcpus") or not specs.get("memoryGB"):
            search_text = f"{product_name or ''} {sku_name or ''}".lower()
            
            if not specs.get("vcpus"):
                vcpu_match = VCPU_PATTERN.search(search_text)
                if vcpu_match:
                    try:
                        specs["vcpus"] = int(vcpu_match.group(1))
                    except (ValueError, TypeError): pass
            
            if not specs.get("memoryGB"):
                ram_match = RAM_PATTERN.search(search_text)
                if ram_match:
                    try:
                        specs["memoryGB"] = float(ram_match.group(1))
                    except (ValueError, TypeError): pass
        
        return specs
    
    def determine_os_type(self, product_name: str, sku_name: str) -> str:
        combined_text = f"{product_name or ''} {sku_name or ''}".lower()
        if "windows" in combined_text:
            return "Windows"
        
        linux_indicators = ["linux", "ubuntu", "red hat", "rhel", "suse", "debian", "centos"]
        if any(indicator in combined_text for indicator in linux_indicators):
            return "Linux"
            
        return "Unknown"
    
    def is_spot_instance(self, sku_name: str, product_name: str) -> bool:
        combined_text = f"{sku_name or ''} {product_name or ''}".lower()
        return any(indicator in combined_text for indicator in ["spot", "low priority"])
    
    def extract_series_info(self, sku_name: str, arm_sku_name: str) -> Dict[str, Optional[str]]:
        source_text = arm_sku_name or sku_name or ""
        series_match = SERIES_PATTERN.search(source_text)
        if series_match:
            family = series_match.group(1).upper()
            generation = series_match.group(2)
            series = f"{family}v{generation}"
        else:
            family_match = re.match(r'([A-Za-z]+)', source_text.replace("Standard_", ""))
            family = family_match.group(1).upper() if family_match else None
            series = family
        
        return {"series": series, "family": family, "size": arm_sku_name or sku_name}
    
    def fetch_vm_prices(self, os_filter: str = "both", include_spot: bool = False, 
                        regions: Optional[List[str]] = None, max_pages: int = 0, 
                        timeout: int = 30) -> List[Dict[str, Any]]:
        all_items = []
        next_url = None
        page_count = 0
        
        # RESTORED: Generate random page limit if max_pages is 0
        if max_pages == 0:
            max_pages = random.randint(10, 100)
            print(f"Random page limit set to: {max_pages} pages")
        
        query_filter = self.build_query_filter(os_filter)
        params = {"$filter": query_filter, "currencyCode": "USD"}
        
        print(f"Starting data collection with filter: {query_filter}")
        print(f"Page limit: {max_pages} pages")
        
        while True:
            page_count += 1
            if page_count > max_pages:
                print(f"Reached maximum page limit ({max_pages})")
                break
            
            url = next_url or AZURE_API_URL
            current_params = {} if next_url else params
            
            try:
                response = self.session.get(url, params=current_params, timeout=timeout)
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
                    print("No more pages available.")
                    break
                
                time.sleep(0.3)
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page_count}: {e}", file=sys.stderr)
                break
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on page {page_count}: {e}", file=sys.stderr)
                break
        
        print(f"Data collection complete. Total items: {len(all_items)}")
        return all_items
    
    def _should_include_item(self, item: Dict[str, Any], include_spot: bool, 
                             regions: Optional[List[str]]) -> bool:
        if item.get("serviceName") != "Virtual Machines" or not self.is_consumption_pricing(item):
            return False
        
        if not include_spot and self.is_spot_instance(item.get("skuName", ""), item.get("productName", "")):
            return False
        
        if regions:
            item_region = item.get("armRegionName") or item.get("location", "")
            if not item_region or item_region.lower() not in [r.lower() for r in regions]:
                return False
        
        return True
    
    def _process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sku_name = item.get("skuName", "")
            product_name = item.get("productName", "")
            arm_sku_name = item.get("armSkuName", "")
            
            series_info = self.extract_series_info(sku_name, arm_sku_name)
            vm_name = series_info["size"] or sku_name or arm_sku_name
            
            specs = self.parse_vm_specs(product_name, sku_name, vm_name)
            os_type = self.determine_os_type(product_name, sku_name)
            is_spot = self.is_spot_instance(sku_name, product_name)
            
            price = float(item.get("retailPrice") or item.get("unitPrice") or 0.0)
            if price > 1000: return None
            
            return {
                "name": vm_name, "family": series_info["family"], "os": os_type,
                "isSpot": is_spot, "vcpus": specs.get("vcpus"), "memoryGB": specs.get("memoryGB"),
                "pricePerHour": price, "region": item.get("armRegionName") or item.get("location", ""),
                # You can add other fields from the 'item' dictionary here if needed
            }
        except Exception as e:
            print(f"Warning: Could not process item {item.get('skuId')}. Reason: {e}", file=sys.stderr)
            return None
    
    def generate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not items: return {}
        
        prices = [item["pricePerHour"] for item in items if "pricePerHour" in item]
        regions = sorted(list(set(item["region"] for item in items if item.get("region"))))
        families = sorted(list(set(item["family"] for item in items if item.get("family"))))
        os_types = sorted(list(set(item["os"] for item in items if item.get("os"))))
        
        return {
            "count": len(items),
            "regionsCount": len(regions),
            "regions": regions,
            "familiesCount": len(families),
            "families": families,
            "osTypes": os_types,
            "spotCount": sum(1 for item in items if item.get("isSpot")),
            "avgPricePerHour": round(sum(prices) / len(prices), 6) if prices else 0,
            "minPricePerHour": round(min(prices), 6) if prices else 0,
            "maxPricePerHour": round(max(prices), 6) if prices else 0,
        }
    
    def save_to_json(self, items: List[Dict[str, Any]], filename: str) -> None:
        metadata = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": AZURE_API_URL,
            "itemCount": len(items),
            "summary": self.generate_summary(items)
        }
        
        output = {"metadata": metadata, "items": items}
        
        # FIXED: Ensure the output directory exists before writing the file
        output_dir = os.path.dirname(filename)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Azure VM Price Scanner - OPTIMIZED")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_RELATIVE, help="Output JSON file path")
    parser.add_argument("--os", choices=["linux", "windows", "both"], default="both", help="OS filter")
    parser.add_argument("--include-spot", action="store_true", help="Include Spot instances")
    parser.add_argument("--regions", type=str, default="", help="Comma-separated list of regions")
    parser.add_argument("--max-pages", type=int, default=0, help="Maximum pages to fetch (0 = random 10-100)")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    
    args = parser.parse_args()
    
    regions_list = [r.strip().lower() for r in args.regions.split(",") if r.strip()] if args.regions else None
    
    # FIXED: Build a reliable, absolute path for the output file
    if args.out == DEFAULT_OUTPUT_RELATIVE:
        script_dir = os.path.dirname(__file__)
        output_file_path = os.path.join(script_dir, args.out)
        output_file_path = os.path.normpath(output_file_path)
    else:
        output_file_path = args.out
    
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
        
        if items:
            scanner.save_to_json(items, output_file_path)
            summary = scanner.generate_summary(items)
            print("\n=== COLLECTION SUMMARY ===")
            print(f"Total VMs Processed: {summary.get('count', 0)}")
            print(f"Duration: {time.time() - start_time:.2f} seconds")
        else:
            print("No items were collected.")
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()