"""
Final demonstration of SFC License Integration in the Chatbot
"""
import sys
import os

# Add the App directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'App'))

from chatbot_service import candidate_chatbot

def demo_sfc_integration():
    """Demonstrate the complete SFC license integration functionality"""
    
    print("🚀 SFC License Integration Demo")
    print("=" * 60)
    print("This demonstrates the complete workflow:")
    print("1. User asks about SFC license")
    print("2. Intent classifier identifies 'sfc_license' intent")
    print("3. Name extraction specialist extracts candidate name")
    print("4. SFC search function performs automated web scraping")
    print("5. Response specialist generates user-friendly answer")
    print("\n" + "=" * 60)
    
    # Test cases with different name formats and query styles
    test_cases = [
        {
            "description": "Known SFC license holder (should show ACTIVE SFO license)",
            "query": "Does POON Kwok Tung have an SFC license?"
        },
        {
            "description": "Different query format",
            "query": "Check POON Kwok Tung's SFC license status"
        },
        {
            "description": "Alternative phrasing", 
            "query": "Is POON Kwok Tung SFC licensed?"
        },
        {
            "description": "Person without SFC license (should show no license found)",
            "query": "Does John Smith have an SFC license?"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['description']}")
        print("-" * 50)
        print(f"Query: '{test_case['query']}'")
        print("\nResponse:")
        
        try:
            response = candidate_chatbot.chat(test_case['query'])
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
        
        # Add a pause between tests for readability
        if i < len(test_cases):
            input("\nPress Enter to continue to next test case...")

def show_integration_summary():
    """Show a summary of what was integrated"""
    
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION SUMMARY")
    print("=" * 60)
    print("✅ Intent Classification: Added 'sfc_license' intent detection")
    print("✅ Name Extraction: Enhanced to handle various name formats (CAPS, Mixed)")
    print("✅ SFC Web Automation: Integrated working sfc_search() function")
    print("✅ Response Generation: Creates formatted responses with license status")
    print("✅ Error Handling: Graceful fallbacks for failed checks")
    print("✅ Manual Verification: Always provides SFC website link")
    
    print("\n🔄 WORKFLOW:")
    print("User Query → Intent Analysis → Name Extraction → SFC Search → Response")
    
    print("\n📋 SUPPORTED QUERY TYPES:")
    print("• 'Does [NAME] have an SFC license?'")
    print("• 'Check [NAME]'s SFC license'")
    print("• 'Is [NAME] SFC licensed?'")
    print("• 'SFC license verification for [NAME]'")
    
    print("\n📊 LICENSE TYPES CHECKED:")
    print("• SFO License (Securities and Futures Ordinance)")
    print("• AMLO License (Anti-Money Laundering)")
    
    print("\n🌐 Manual Verification Always Available:")
    print("• https://apps.sfc.hk/publicregWeb/searchByName")

if __name__ == "__main__":
    if candidate_chatbot.is_available():
        show_integration_summary()
        
        print("\n" + "=" * 60)
        start_demo = input("Ready to start the demo? (y/n): ").lower().strip()
        
        if start_demo == 'y':
            demo_sfc_integration()
        else:
            print("Demo cancelled. Integration is ready for use!")
    else:
        print("❌ Chatbot is not available. Please check your configuration.")
        status = candidate_chatbot.get_specialists_status()
        print("Specialists status:", status) 