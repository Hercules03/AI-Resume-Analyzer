"""
SFC License checking specialists for automated license verification.
"""
from typing import Type, Optional, Dict, Any, List
from .base_specialist import BaseSpecialist
from .models import SFCLicenseQuery, SFCLicenseResult
from pydantic import BaseModel
import re

class SFCLicenseCheckSpecialist(BaseSpecialist):
    """Specialist for performing SFC license verification via web automation."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """No structured output needed for web automation."""
        return None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for SFC license checking."""
        return """You are an SFC license verification specialist. You help interpret the results of automated SFC license checks performed via the official SFC website.

**Your Role:**
- Analyze search results from SFC public register
- Determine if a person holds a valid SFC license
- Provide clear, factual responses about license status
- Include verification links for manual checking

**Response Guidelines:**
- Be factual and precise about license status
- Always include the search URL for manual verification
- Mention any limitations or uncertainties in the automated check
- Provide helpful context about SFC licensing if relevant"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for SFC license verification."""
        return """Based on the SFC license check results, provide a clear response about the license status for the user.

Candidate Name: {candidate_name}
SFO License Status: {sfo_license}
AMLO License Status: {amlo_license}
Check Success: {success}
Error Message: {error_message}
Search URL: {search_url}

Generate a user-friendly response that includes:
1. Clear status of SFO and AMLO licenses (Active/Not Active/Unknown)
2. Professional explanation of what each license means
3. Manual verification link
4. Appropriate formatting with emojis and clear structure"""
    
    def prepare_input_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare input data for SFC license verification response."""
        check_results = kwargs.get('check_results', {})
        return {
            'candidate_name': check_results.get('candidate_name', ''),
            'sfo_license': check_results.get('sfo_license', 'Unknown'),
            'amlo_license': check_results.get('amlo_license', 'Unknown'),
            'success': check_results.get('success', False),
            'error_message': check_results.get('error', 'None'),
            'search_url': check_results.get('search_url', 'https://apps.sfc.hk/publicregWeb/searchByName')
        }
    
    def process_output(self, output: str, **kwargs) -> str:
        """Process the SFC license verification response."""
        if output and output.strip():
            return output.strip()
        
        # Fallback: Generate structured response based on check results
        check_results = kwargs.get('check_results', {})
        return self._generate_structured_response(check_results)
    
    def _generate_structured_response(self, check_results: Dict[str, Any]) -> str:
        """Generate a structured response based on check results."""
        candidate_name = check_results.get('candidate_name', 'the candidate')
        success = check_results.get('success', False)
        sfo_license = check_results.get('sfo_license', 'Unknown')
        amlo_license = check_results.get('amlo_license', 'Unknown')
        error_message = check_results.get('error', '')
        search_url = check_results.get('search_url', 'https://apps.sfc.hk/publicregWeb/searchByName')
        
        if not success:
            if "No license records found" in error_message:
                return f"""**SFC License Verification for {candidate_name}**

❌ **No License Found** - No SFC license records were found for this candidate in the public register.

This means the candidate:
- Does not currently hold an SFC license
- May have never been licensed by the SFC
- Name might not match exactly with registered records

**Manual Verification:** You can double-check at: {search_url}

*Note: Please ensure the name spelling is correct, as the search is case-sensitive.*"""
            else:
                return f"""**SFC License Check - Technical Issue**

I encountered a technical issue while checking the SFC license status for {candidate_name}.

**Manual Verification:** Please check manually at: {search_url}

1. Enter the candidate's full name
2. Select "Individual" 
3. Click "Search"

*Error details: {error_message}*"""
        
        # Successful check - format the response
        response_parts = [f"**SFC License Verification for {candidate_name}**\n"]
        
        if sfo_license == "Active":
            response_parts.append("✅ **SFO License: ACTIVE** - This candidate holds a valid SFC license for dealing in securities.")
        elif sfo_license == "Not Active":
            response_parts.append("❌ **SFO License: NOT ACTIVE** - This candidate does not currently hold an active SFC license for dealing in securities.")
        else:
            response_parts.append("❓ **SFO License: STATUS UNCLEAR** - Unable to determine SFO license status clearly.")
        
        if amlo_license == "Active":
            response_parts.append("✅ **AMLO License: ACTIVE** - This candidate holds a valid license under the Anti-Money Laundering and Counter-Terrorist Financing Ordinance.")
        elif amlo_license == "Not Active":
            response_parts.append("❌ **AMLO License: NOT ACTIVE** - This candidate does not currently hold an active AMLO license.")
        else:
            response_parts.append("❓ **AMLO License: STATUS UNCLEAR** - Unable to determine AMLO license status clearly.")
        
        response_parts.extend([
            f"\n**Manual Verification:** You can verify this information manually at: {search_url}",
            "\n*Note: This automated check was performed using the official SFC public register. License statuses can change, so please verify manually for the most current information.*"
        ])
        
        return "\n".join(response_parts)
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when SFC license verification fails."""
        candidate_name = kwargs.get('candidate_name', 'the candidate')
        return f"""I'm unable to verify the SFC license status for {candidate_name} at the moment due to technical issues.

You can manually check their license status at:
https://apps.sfc.hk/publicregWeb/searchByName

Please enter their name in the search form to verify their registration status."""


class SFCWebAutomationService:
    """Service for automated SFC license checking via web scraping using the working sfc_search function."""
    
    def __init__(self):
        """Initialize the SFC web automation service."""
        self.base_url = "https://apps.sfc.hk/publicregWeb/searchByName"
    
    def check_sfc_license(self, candidate_name: str) -> Dict[str, Any]:
        """
        Perform automated SFC license check using the working sfc_search function.
        
        Args:
            candidate_name: Name of the person to check
            
        Returns:
            Dictionary with check results
        """
        try:
            # Import required modules for subprocess execution
            import sys
            import os
            import io
            import subprocess
            import tempfile
            
            # Run the sfc_search function in a separate process to avoid signal conflicts
            try:
                import subprocess
                import json
                import tempfile
                
                # Create a subprocess script to run sfc_search
                script_content = f'''
import asyncio
import sys
import os
import json

# Add the current working directory (App directory) to path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

from sfc_search import sfc_search

async def main():
    try:
        # Capture the output from sfc_search function
        import io
        import contextlib
        
        # Redirect stdout to capture the sfc_search output
        captured_output = io.StringIO()
        
        with contextlib.redirect_stdout(captured_output):
            await sfc_search("{candidate_name}")
        
        # Get the captured output and print it so parent process can capture it
        output_text = captured_output.getvalue()
        print(output_text)
        print("SFC_SEARCH_COMPLETED")
        
    except Exception as e:
        print(f"SFC_SEARCH_ERROR: {{str(e)}}")

if __name__ == "__main__":
    asyncio.run(main())
'''
                
                # Write the script to a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(script_content)
                    script_path = f.name
                
                try:
                    # Run the subprocess with proper working directory (App directory)
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    app_dir = os.path.dirname(current_dir)  # Go up one level from db_specialists to App
                    
                    process = subprocess.run(
                        [sys.executable, script_path],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=app_dir
                    )
                    
                    # Get the captured output
                    output_text = process.stdout
                    
                    # Clean up the temporary script
                    os.unlink(script_path)
                    
                    captured_output = io.StringIO()
                    captured_output.write(output_text)
                    
                except subprocess.TimeoutExpired:
                    # Clean up the temporary script
                    os.unlink(script_path)
                    return {
                        'success': False,
                        'error': 'SFC search timed out after 60 seconds',
                        'candidate_name': candidate_name,
                        'search_url': self.base_url
                    }
                except Exception as e:
                    # Clean up the temporary script
                    if os.path.exists(script_path):
                        os.unlink(script_path)
                    return {
                        'success': False,
                        'error': f'Subprocess execution failed: {str(e)}',
                        'candidate_name': candidate_name,
                        'search_url': self.base_url
                    }
                
                # Parse the captured output to determine results
                output_text = captured_output.getvalue()
                
                # Analyze the output to determine license status
                sfo_license = "Unknown"
                amlo_license = "Unknown"
                success = True
                error_message = None
                
                if "NO LICENSE FOUND" in output_text:
                    success = False
                    error_message = "No license records found in SFC register"
                elif "LICENSE FOUND" in output_text or "SFO License Status:" in output_text:
                    # Extract SFO license status
                    if "ACTIVE SFO LICENSE CONFIRMED" in output_text or "SFO License Status: Yes" in output_text:
                        sfo_license = "Active"
                    elif "NO ACTIVE SFO LICENSE" in output_text or "SFO License Status: No" in output_text:
                        sfo_license = "Not Active"
                    
                    # Extract AMLO license status  
                    if "ACTIVE AMLO LICENSE CONFIRMED" in output_text or "AMLO License Status: Yes" in output_text:
                        amlo_license = "Active"
                    elif "NO ACTIVE AMLO LICENSE" in output_text or "AMLO License Status: No" in output_text:
                        amlo_license = "Not Active"
                elif "Result: UNKNOWN" in output_text or "failed" in output_text.lower():
                    success = False
                    error_message = "License check failed or returned unclear results"
                
                # Return structured results
                result = {
                    'success': success,
                    'candidate_name': candidate_name,
                    'sfo_license': sfo_license,
                    'amlo_license': amlo_license,
                    'raw_output': output_text,
                    'search_url': self.base_url
                }
                
                if error_message:
                    result['error'] = error_message
                
                return result
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'SFC license check failed: {str(e)}',
                    'candidate_name': candidate_name,
                    'search_url': self.base_url
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Automation failed: {str(e)}',
                'candidate_name': candidate_name,
                'search_url': self.base_url
            }
    
    def format_check_url(self, candidate_name: str) -> str:
        """Format the manual check URL with pre-filled name if possible."""
        # Note: Some websites support URL parameters for pre-filling forms
        # You may need to check if SFC supports this
        return f"{self.base_url}?name={candidate_name.replace(' ', '+')}"