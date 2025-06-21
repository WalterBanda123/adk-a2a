#!/usr/bin/env python3

"""
Simple test to verify the parsing fix
"""

def test_parsing_patterns():
    import re
    
    # Test the original message and after cleaning
    original_message = "sold Huletts sugar @3.4"
    cleaned_message = original_message.replace('sold ', '')  # Should become "Huletts sugar @3.4"
    
    print(f"Original: '{original_message}'")
    print(f"Cleaned: '{cleaned_message}'")
    
    # Test the patterns
    patterns = [
        r'(\d+)\s+((?:\w+\s*){1,5})\s+@\s*(\d+(?:\.\d+)?)',  # "2 mazoe orange crush @ 3.50"
        r'(\d+)\s+((?:\w+\s*){1,5})\s+(?:by|for|at)\s+(\d+(?:\.\d+)?)',  # "2 mazoe orange crush by 3.50"
        r'(\d+)\s+((?:\w+\s*){1,5})(?:\s*,|$)',  # "2 mazoe orange crush," or end of string
        r'((?:\w+\s*){1,5})\s+@\s*(\d+(?:\.\d+)?)',  # "huletts sugar @ 3.4" (quantity = 1)
        r'((?:\w+\s*){1,5})\s+(?:by|for|at)\s+(\d+(?:\.\d+)?)',  # "huletts sugar by 3.4" (quantity = 1)
    ]
    
    print(f"\nTesting patterns against: '{cleaned_message}'")
    
    for i, pattern in enumerate(patterns):
        print(f"\nPattern {i+1}: {pattern}")
        match = re.search(pattern, cleaned_message, re.IGNORECASE)
        
        if match:
            groups = match.groups()
            print(f"  ✅ MATCHED! Groups: {groups}")
            
            # Handle patterns with explicit quantity vs implicit quantity=1
            if len(groups) == 3:  # Standard pattern: (quantity, name, price)
                try:
                    quantity = int(groups[0])
                    raw_name = groups[1].strip()
                    unit_price = float(groups[2]) if groups[2] else None
                    print(f"  📦 Parsed: {quantity} x '{raw_name}' @ ${unit_price}")
                except ValueError as e:
                    print(f"  ❌ Parse error: {e}")
            elif len(groups) == 2:  # No explicit quantity: (name, price)
                try:
                    quantity = 1  # Default to 1 when no quantity specified
                    raw_name = groups[0].strip()
                    unit_price = float(groups[1]) if groups[1] else None
                    print(f"  📦 Parsed: {quantity} x '{raw_name}' @ ${unit_price}")
                except ValueError as e:
                    print(f"  ❌ Parse error: {e}")
            else:
                print(f"  ⚠️  Unexpected group count: {len(groups)}")
        else:
            print(f"  ❌ No match")

if __name__ == "__main__":
    test_parsing_patterns()
