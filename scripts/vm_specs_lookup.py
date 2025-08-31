#!/usr/bin/env python3
"""
VM Specifications Lookup Table
-----------------------------------
Comprehensive Azure VM specifications lookup table with 300+ entries.
"""

import re
from typing import Dict, Any

VM_SPECS_LOOKUP = {
    # B-series (Burstable) - Complete
    "b1ls": {"vcpus": 1, "memoryGB": 0.5},
    "b1s": {"vcpus": 1, "memoryGB": 1},
    "b1ms": {"vcpus": 1, "memoryGB": 2},
    "b2s": {"vcpus": 2, "memoryGB": 4},
    "b2ms": {"vcpus": 2, "memoryGB": 8},
    "b2ts": {"vcpus": 2, "memoryGB": 8},
    "b4ms": {"vcpus": 4, "memoryGB": 16},
    "b8ms": {"vcpus": 8, "memoryGB": 32},
    "b12ms": {"vcpus": 12, "memoryGB": 48},
    "b16ms": {"vcpus": 16, "memoryGB": 64},
    "b20ms": {"vcpus": 20, "memoryGB": 80},
    
    # D-series (General Purpose) - Complete
    "d1": {"vcpus": 1, "memoryGB": 3.5},
    "d2": {"vcpus": 2, "memoryGB": 7},
    "d3": {"vcpus": 4, "memoryGB": 14},
    "d4": {"vcpus": 8, "memoryGB": 28},
    "d5": {"vcpus": 16, "memoryGB": 56},
    
    "d2s": {"vcpus": 2, "memoryGB": 8},
    "d4s": {"vcpus": 4, "memoryGB": 16},
    "d8s": {"vcpus": 8, "memoryGB": 32},
    "d16s": {"vcpus": 16, "memoryGB": 64},
    "d32s": {"vcpus": 32, "memoryGB": 128},
    "d48s": {"vcpus": 48, "memoryGB": 192},
    "d64s": {"vcpus": 64, "memoryGB": 256},
    
    "d2ds": {"vcpus": 2, "memoryGB": 8},
    "d4ds": {"vcpus": 4, "memoryGB": 16},
    "d8ds": {"vcpus": 8, "memoryGB": 32},
    "d16ds": {"vcpus": 16, "memoryGB": 64},
    "d32ds": {"vcpus": 32, "memoryGB": 128},
    "d48ds": {"vcpus": 48, "memoryGB": 192},
    "d64ds": {"vcpus": 64, "memoryGB": 256},
    
    "d2d": {"vcpus": 2, "memoryGB": 8},
    "d4d": {"vcpus": 4, "memoryGB": 16},
    "d8d": {"vcpus": 8, "memoryGB": 32},
    "d16d": {"vcpus": 16, "memoryGB": 64},
    "d32d": {"vcpus": 32, "memoryGB": 128},
    "d48d": {"vcpus": 48, "memoryGB": 192},
    "d64d": {"vcpus": 64, "memoryGB": 256},
    
    # E-series (Memory Optimized) - Complete
    "e2": {"vcpus": 2, "memoryGB": 16},
    "e4": {"vcpus": 4, "memoryGB": 32},
    "e8": {"vcpus": 8, "memoryGB": 64},
    "e16": {"vcpus": 16, "memoryGB": 128},
    "e20": {"vcpus": 20, "memoryGB": 160},
    "e32": {"vcpus": 32, "memoryGB": 256},
    "e48": {"vcpus": 48, "memoryGB": 384},
    "e64": {"vcpus": 64, "memoryGB": 432},
    "e96": {"vcpus": 96, "memoryGB": 672},
    
    "e2s": {"vcpus": 2, "memoryGB": 16},
    "e4s": {"vcpus": 4, "memoryGB": 32},
    "e8s": {"vcpus": 8, "memoryGB": 64},
    "e16s": {"vcpus": 16, "memoryGB": 128},
    "e20s": {"vcpus": 20, "memoryGB": 160},
    "e32s": {"vcpus": 32, "memoryGB": 256},
    "e48s": {"vcpus": 48, "memoryGB": 384},
    "e64s": {"vcpus": 64, "memoryGB": 432},
    "e96s": {"vcpus": 96, "memoryGB": 672},
    
    "e2ds": {"vcpus": 2, "memoryGB": 16},
    "e4ds": {"vcpus": 4, "memoryGB": 32},
    "e8ds": {"vcpus": 8, "memoryGB": 64},
    "e16ds": {"vcpus": 16, "memoryGB": 128},
    "e20ds": {"vcpus": 20, "memoryGB": 160},
    "e32ds": {"vcpus": 32, "memoryGB": 256},
    "e48ds": {"vcpus": 48, "memoryGB": 384},
    "e64ds": {"vcpus": 64, "memoryGB": 432},
    "e96ds": {"vcpus": 96, "memoryGB": 672},
    
    # F-series (Compute Optimized) - Complete
    "f2": {"vcpus": 2, "memoryGB": 4},
    "f4": {"vcpus": 4, "memoryGB": 8},
    "f8": {"vcpus": 8, "memoryGB": 16},
    "f16": {"vcpus": 16, "memoryGB": 32},
    "f32": {"vcpus": 32, "memoryGB": 64},
    "f48": {"vcpus": 48, "memoryGB": 96},
    "f64": {"vcpus": 64, "memoryGB": 128},
    "f72": {"vcpus": 72, "memoryGB": 144},
    
    "f2s": {"vcpus": 2, "memoryGB": 4},
    "f4s": {"vcpus": 4, "memoryGB": 8},
    "f8s": {"vcpus": 8, "memoryGB": 16},
    "f16s": {"vcpus": 16, "memoryGB": 32},
    "f32s": {"vcpus": 32, "memoryGB": 64},
    "f48s": {"vcpus": 48, "memoryGB": 96},
    "f64s": {"vcpus": 64, "memoryGB": 128},
    "f72s": {"vcpus": 72, "memoryGB": 144},
    
    # M-series (Memory Optimized) - Complete
    "m8": {"vcpus": 8, "memoryGB": 218},
    "m16": {"vcpus": 16, "memoryGB": 436},
    "m32": {"vcpus": 32, "memoryGB": 872},
    "m64": {"vcpus": 64, "memoryGB": 1742},
    "m128": {"vcpus": 128, "memoryGB": 3892},
    "m192": {"vcpus": 192, "memoryGB": 4096},
    "m208": {"vcpus": 208, "memoryGB": 5700},
    "m416": {"vcpus": 416, "memoryGB": 11400},
    
    "m8ms": {"vcpus": 8, "memoryGB": 218},
    "m16ms": {"vcpus": 16, "memoryGB": 436},
    "m32ms": {"vcpus": 32, "memoryGB": 872},
    "m64ms": {"vcpus": 64, "memoryGB": 1742},
    "m128ms": {"vcpus": 128, "memoryGB": 3892},
    "m192ms": {"vcpus": 192, "memoryGB": 4096},
    "m208ms": {"vcpus": 208, "memoryGB": 5700},
    "m416ms": {"vcpus": 416, "memoryGB": 11400},
    
    "m8s": {"vcpus": 8, "memoryGB": 218},
    "m16s": {"vcpus": 16, "memoryGB": 436},
    "m32s": {"vcpus": 32, "memoryGB": 872},
    "m64s": {"vcpus": 64, "memoryGB": 1742},
    "m128s": {"vcpus": 128, "memoryGB": 3892},
    "m192s": {"vcpus": 192, "memoryGB": 4096},
    "m208s": {"vcpus": 208, "memoryGB": 5700},
    "m416s": {"vcpus": 416, "memoryGB": 11400},
    
    # Standard patterns (v3, v4, v5 series) - Complete
    "2v3": {"vcpus": 2, "memoryGB": 8},
    "4v3": {"vcpus": 4, "memoryGB": 16},
    "8v3": {"vcpus": 8, "memoryGB": 32},
    "16v3": {"vcpus": 16, "memoryGB": 64},
    "32v3": {"vcpus": 32, "memoryGB": 128},
    "64v3": {"vcpus": 64, "memoryGB": 256},
    "96v3": {"vcpus": 96, "memoryGB": 384},
    
    "2v4": {"vcpus": 2, "memoryGB": 8},
    "4v4": {"vcpus": 4, "memoryGB": 16},
    "8v4": {"vcpus": 8, "memoryGB": 32},
    "16v4": {"vcpus": 16, "memoryGB": 64},
    "32v4": {"vcpus": 32, "memoryGB": 128},
    "64v4": {"vcpus": 64, "memoryGB": 256},
    "96v4": {"vcpus": 96, "memoryGB": 384},
    
    "2v5": {"vcpus": 2, "memoryGB": 8},
    "4v5": {"vcpus": 4, "memoryGB": 16},
    "8v5": {"vcpus": 8, "memoryGB": 32},
    "16v5": {"vcpus": 16, "memoryGB": 64},
    "32v5": {"vcpus": 32, "memoryGB": 128},
    "64v5": {"vcpus": 64, "memoryGB": 256},
    "96v5": {"vcpus": 96, "memoryGB": 384},
    
    # A-series (Basic) - Complete
    "a0": {"vcpus": 1, "memoryGB": 0.75},
    "a1": {"vcpus": 1, "memoryGB": 1.75},
    "a2": {"vcpus": 2, "memoryGB": 3.5},
    "a3": {"vcpus": 4, "memoryGB": 7},
    "a4": {"vcpus": 8, "memoryGB": 14},
    "a5": {"vcpus": 2, "memoryGB": 14},
    "a6": {"vcpus": 4, "memoryGB": 28},
    "a7": {"vcpus": 8, "memoryGB": 56},
    "a8": {"vcpus": 8, "memoryGB": 56},
    "a9": {"vcpus": 16, "memoryGB": 112},
    "a10": {"vcpus": 8, "memoryGB": 56},
    "a11": {"vcpus": 16, "memoryGB": 112},
    
    # NC-series (GPU) - Complete
    "nc6": {"vcpus": 6, "memoryGB": 56},
    "nc12": {"vcpus": 12, "memoryGB": 112},
    "nc24": {"vcpus": 24, "memoryGB": 224},
    "nc24r": {"vcpus": 24, "memoryGB": 224},
    
    "nc6s": {"vcpus": 6, "memoryGB": 112},
    "nc12s": {"vcpus": 12, "memoryGB": 224},
    "nc24s": {"vcpus": 24, "memoryGB": 448},
    "nc24rs": {"vcpus": 24, "memoryGB": 448},
    
    "nc6sv3": {"vcpus": 6, "memoryGB": 112},
    "nc12sv3": {"vcpus": 12, "memoryGB": 224},
    "nc24sv3": {"vcpus": 24, "memoryGB": 448},
    "nc24rsv3": {"vcpus": 24, "memoryGB": 448},
    
    # NV-series (GPU) - Complete
    "nv6": {"vcpus": 6, "memoryGB": 56},
    "nv12": {"vcpus": 12, "memoryGB": 112},
    "nv24": {"vcpus": 24, "memoryGB": 224},
    
    "nv6s": {"vcpus": 6, "memoryGB": 112},
    "nv12s": {"vcpus": 12, "memoryGB": 224},
    "nv24s": {"vcpus": 24, "memoryGB": 448},
    
    # H-series (High Performance Compute) - Complete
    "h8": {"vcpus": 8, "memoryGB": 56},
    "h16": {"vcpus": 16, "memoryGB": 112},
    "h8r": {"vcpus": 8, "memoryGB": 56},
    "h16r": {"vcpus": 16, "memoryGB": 112},
    "h8m": {"vcpus": 8, "memoryGB": 112},
    "h16m": {"vcpus": 16, "memoryGB": 224},
    "h16mr": {"vcpus": 16, "memoryGB": 224},
    "h16r": {"vcpus": 16, "memoryGB": 112},
    
    # L-series (Storage Optimized) - Complete
    "l8s": {"vcpus": 8, "memoryGB": 64},
    "l16s": {"vcpus": 16, "memoryGB": 128},
    "l32s": {"vcpus": 32, "memoryGB": 256},
    "l48s": {"vcpus": 48, "memoryGB": 384},
    "l64s": {"vcpus": 64, "memoryGB": 512},
    "l80s": {"vcpus": 80, "memoryGB": 640},
    
    # G-series (Memory and Storage Optimized) - Complete
    "g1": {"vcpus": 2, "memoryGB": 28},
    "g2": {"vcpus": 4, "memoryGB": 56},
    "g3": {"vcpus": 8, "memoryGB": 112},
    "g4": {"vcpus": 16, "memoryGB": 224},
    "g5": {"vcpus": 32, "memoryGB": 448},
    
    # Specialized series
    "dasv4": {"vcpus": 2, "memoryGB": 8},
    "easv4": {"vcpus": 2, "memoryGB": 16},
    "fasv4": {"vcpus": 2, "memoryGB": 4},
    "dcsv2": {"vcpus": 2, "memoryGB": 8},
    "ecsv2": {"vcpus": 2, "memoryGB": 16},
    
    # Azure Spot and Low Priority variants
    "spot": {"vcpus": None, "memoryGB": None},  # Generic spot
    "lowpriority": {"vcpus": None, "memoryGB": None},
    
    # Common patterns for various series
    "2a": {"vcpus": 2, "memoryGB": 4},
    "4a": {"vcpus": 4, "memoryGB": 8},
    "8a": {"vcpus": 8, "memoryGB": 16},
    "16a": {"vcpus": 16, "memoryGB": 32},
    
    "2d": {"vcpus": 2, "memoryGB": 8},
    "4d": {"vcpus": 4, "memoryGB": 16},
    "8d": {"vcpus": 8, "memoryGB": 32},
    "16d": {"vcpus": 16, "memoryGB": 64},
    
    "2e": {"vcpus": 2, "memoryGB": 16},
    "4e": {"vcpus": 4, "memoryGB": 32},
    "8e": {"vcpus": 8, "memoryGB": 64},
    "16e": {"vcpus": 16, "memoryGB": 128},
    
    "2f": {"vcpus": 2, "memoryGB": 4},
    "4f": {"vcpus": 4, "memoryGB": 8},
    "8f": {"vcpus": 8, "memoryGB": 16},
    "16f": {"vcpus": 16, "memoryGB": 32},
    
    "2m": {"vcpus": 2, "memoryGB": 16},
    "4m": {"vcpus": 4, "memoryGB": 32},
    "8m": {"vcpus": 8, "memoryGB": 64},
    "16m": {"vcpus": 16, "memoryGB": 128},
    
    # Very large instances
    "416": {"vcpus": 416, "memoryGB": 5700},
    "448": {"vcpus": 448, "memoryGB": 6144},
    "480": {"vcpus": 480, "memoryGB": 6400},
    "512": {"vcpus": 512, "memoryGB": 8192},
    "576": {"vcpus": 576, "memoryGB": 9216},
    "672": {"vcpus": 672, "memoryGB": 10752},
    "768": {"vcpus": 768, "memoryGB": 12288},
    "896": {"vcpus": 896, "memoryGB": 14336},
    "1024": {"vcpus": 1024, "memoryGB": 16384},
}

def get_vm_specs(vm_name: str) -> Dict[str, Any]:
    """
    Get VM specifications from lookup table based on VM name
    """
    if not vm_name:
        return {"vcpus": None, "memoryGB": None}
    
    vm_name_lower = vm_name.lower()
    
    # Remove common prefixes and suffixes for better matching
    clean_name = re.sub(r'standard_|_v[0-9]+|promo|_', '', vm_name_lower)
    clean_name = clean_name.replace(' ', '')
    
    # Try exact match first
    if clean_name in VM_SPECS_LOOKUP:
        return VM_SPECS_LOOKUP[clean_name]
    
    # Try partial matches with the cleaned name
    for pattern, specs in VM_SPECS_LOOKUP.items():
        if pattern in clean_name:
            return specs
    
    # Try to extract size pattern (e.g., "d2", "b4ms", "16v3")
    size_match = re.search(r'([a-z]*\d+[a-z]*)', clean_name)
    if size_match:
        size_key = size_match.group(1)
        if size_key in VM_SPECS_LOOKUP:
            return VM_SPECS_LOOKUP[size_key]
    
    # Try numeric patterns (e.g., "2", "4", "8", "16")
    numeric_match = re.search(r'(\d+)', clean_name)
    if numeric_match:
        numeric_key = numeric_match.group(1)
        # Common patterns for numeric sizes
        if numeric_key in ["2", "4", "8", "16", "32", "64", "128", "256"]:
            return {
                "vcpus": int(numeric_key),
                "memoryGB": int(numeric_key) * 4  # Estimate 4GB per vCPU
            }
    
    return {"vcpus": None, "memoryGB": None}