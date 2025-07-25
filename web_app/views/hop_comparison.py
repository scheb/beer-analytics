import json
import os
from django.db import DatabaseError, OperationalError
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.conf import settings

from recipe_db.models import Hop
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.meta import PageMeta


def load_hops_from_json():
    """Load hops data from JSON file, filtering only those with aroma information"""
    try:
        json_path = os.path.join(settings.BASE_DIR, 'recipe_db', 'data', 'hops_aroma.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            hops_data = json.load(f)
        
        # Filter hops that have aroma information (non-empty aromas object)
        hops_with_aromas = []
        for hop in hops_data:
            if hop.get('aromas') and isinstance(hop['aromas'], dict) and hop['aromas']:
                hops_with_aromas.append(hop)
        
        # Sort by name
        hops_with_aromas.sort(key=lambda x: x.get('name', ''))
        
        return hops_with_aromas
    except Exception as e:
        print(f"Error loading hops JSON: {e}")
        return []


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def comparison_tool(request: HttpRequest) -> HttpResponse:
    """Main hop comparison tool page"""
    # Load hops from JSON instead of database
    hops_data = load_hops_from_json()
    
    # Convert to list of dictionaries for template
    hops = []
    for hop in hops_data:
        hops.append({
            'id': hop['name'],  # Use name as ID since we're not using database
            'name': hop['name']
        })

    meta = PageMeta.create(
        "Hop Aroma Comparison Tool", 
        "Compare the aroma profiles of up to 3 different hops using an interactive spider diagram. Analyze flavor notes, alpha acids, and brewing characteristics.",
        keywords=["hops", "comparison", "aroma", "flavors", "brewing", "analysis"],
        url=reverse("hop_comparison")
    )
    
    context = {
        "hops": hops,
        "meta": meta,
    }
    
    return render(request, "hop/comparison.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def comparison_data(request: HttpRequest) -> JsonResponse:
    """API endpoint to get hop comparison data"""
    hop_names = request.GET.get('hops', '').split(',')
    hop_names = [name.strip() for name in hop_names if name.strip()]
    
    if not hop_names:
        return JsonResponse({"error": "No hops specified"}, status=400)
    
    if len(hop_names) > 3:
        return JsonResponse({"error": "Maximum 3 hops can be compared"}, status=400)
    
    # Load hops from JSON
    hops_data = load_hops_from_json()
    
    if not hops_data:
        return JsonResponse({"error": "Hop data not available"}, status=503)
    
    # Create a lookup dictionary for faster searching
    hops_lookup = {hop['name']: hop for hop in hops_data}
    
    # Filter to requested hops
    selected_hops = []
    for hop_name in hop_names:
        if hop_name in hops_lookup:
            selected_hops.append(hops_lookup[hop_name])
    
    if not selected_hops:
        return JsonResponse({"error": "No matching hops found"}, status=404)
    
    # Get all unique aroma categories across selected hops
    all_aromas = set()
    for hop in selected_hops:
        if hop.get('aromas'):
            all_aromas.update(hop['aromas'].keys())
    
    # Convert to sorted list for consistent ordering
    aroma_categories = sorted(list(all_aromas))
    
    # Build response data
    hops_response = []
    for hop in selected_hops:
        hop_aromas = hop.get('aromas', {})
        
        # Create values for spider chart using actual numerical values
        aroma_values = []
        for category in aroma_categories:
            value = hop_aromas.get(category, 0)
            aroma_values.append(value)
        
        # Extract other hop information
        alpha_from = hop.get('alpha-from', hop.get('alpha_from', 0))
        alpha_to = hop.get('alpha_to', alpha_from)
        
        try:
            alpha_mean = (float(alpha_from) + float(alpha_to)) / 2 if alpha_from and alpha_to else None
        except (ValueError, TypeError):
            alpha_mean = None
        
        hop_data = {
            "name": hop['name'],
            "id": hop['name'],
            "category": "Unknown",  # Not available in JSON
            "origin_countries": [hop.get('country', 'Unknown')] if hop.get('country') else ['Unknown'],
            "aromas": [f"{k} ({v})" for k, v in hop_aromas.items()],  # Include values in display
            "recipes_count": 0,  # Not available from JSON
            "alpha_range": {"mean": alpha_mean},
            "aroma_values": aroma_values,
            "notes": hop.get('notes', [])
        }
        hops_response.append(hop_data)
    
    return JsonResponse({
        "hops": hops_response,
        "aroma_categories": aroma_categories
    })
