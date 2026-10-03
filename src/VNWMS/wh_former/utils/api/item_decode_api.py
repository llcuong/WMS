from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re
from django.utils.translation import gettext_lazy as _, get_language


VENDOR_MAPPING = {
    'A': 'Shinko',
    'B': 'Jinhong', 
    'C': 'Mediceram',
    'D': 'PT',
    'E': 'HL'
}

LENGTH_MAPPING = {
    '38': '380',
    '43': '430'
}

SURFACE_MAPPING = {
    '1': _('Standard Fine Surface'),
    '2': _('Standard Coarse Surface'),
    '3': _('Standard Diamond Textured'),
    '4': _('Energy-saving Fine Surface')
}

TYPE_MAPPING = {
    '1': _('Stainless steel'),
    '2': _('Ceramic')
}

SIZE_MAPPING = {
    '0': 'XXS',
    '1': 'XS',
    '2': 'S',
    '3': 'M',
    '4': 'L',
    '5': 'XL',
    '6': 'XXL',
    '7': 'XXXL'
}


@csrf_exempt
def decode_item_number_api(request):
    item_no = request.GET.get('item_no', '').strip().upper()
    
    if not item_no:
        return JsonResponse({'error': 'Missing item_no parameter'}, status=400)
    
    pattern = r'^F([A-Z])([A-Z])(\d{2})(\d)(\d)(\d)$'
    match = re.match(pattern, item_no)
    
    if not match:
        return JsonResponse({'error': 'Invalid item number format. Expected format: FN[Vendor][Length][Surface][Type][Size]'}, status=400)
    
    try:
        subcategory, vendor_code, length_code, surface_code, type_code, size_code = match.groups()
        
        if subcategory != 'N':
            return JsonResponse({'error': f'Unsupported subcategory: {subcategory}. Only NBR (N) is supported.'}, status=400)
        
        former_vendor = VENDOR_MAPPING.get(vendor_code)
        if not former_vendor:
            return JsonResponse({'error': f'Unknown vendor code: {vendor_code}'}, status=400)
            
        former_length = LENGTH_MAPPING.get(length_code)
        if not former_length:
            return JsonResponse({'error': f'Unknown length code: {length_code}'}, status=400)
            
        former_surface_lazy = SURFACE_MAPPING.get(surface_code)
        if not former_surface_lazy:
            return JsonResponse({'error': f'Unknown surface code: {surface_code}'}, status=400)
        former_surface = str(former_surface_lazy)
            
        former_type_lazy = TYPE_MAPPING.get(type_code)
        if not former_type_lazy:
            return JsonResponse({'error': f'Unknown type code: {type_code}'}, status=400)
        former_type = str(former_type_lazy)
            
        former_size = SIZE_MAPPING.get(size_code)
        if not former_size:
            return JsonResponse({'error': f'Unknown size code: {size_code}'}, status=400)
        
        response_data = {
            'success': True,
            'item_no': item_no,
            'decoded': {
                'category': 'FORMER手模',
                'subcategory': 'NBR',
                'vendor_code': vendor_code,
                'length_code': length_code,
                'surface_code': surface_code,
                'type_code': type_code,
                'size_code': size_code
            },
            'form_data': {
                'former_vendor': former_vendor,
                'former_length': former_length,
                'former_surface': former_surface,
                'former_type': former_type,
                'former_size': former_size,
                'length_value': former_length,
                'vendor_name': former_vendor,
                'params_size': former_size
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': f'Error decoding item number: {str(e)}'}, status=500)


def get_mapping_reference():
    return {
        'pattern': 'FN[Vendor][Length][Surface][Type][Size]',
        'example': 'FNA38124',
        'mappings': {
            'vendor': VENDOR_MAPPING,
            'length': LENGTH_MAPPING,
            'surface': SURFACE_MAPPING,
            'type': TYPE_MAPPING,
            'size': SIZE_MAPPING
        }
    }
