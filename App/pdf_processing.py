"""
PDF processing and text extraction module
Consolidates all PDF extraction logic to eliminate redundancy
"""
import time
import streamlit as st
import pandas as pd
import numpy as np
import cv2
from typing import Optional, Dict, Any, List
from config import OCR_CONFIG, TEXT_QUALITY

# PDF processing imports
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False
    
try:
    import easyocr
    import torch
    EASYOCR_AVAILABLE = True
    GPU_AVAILABLE = torch.cuda.is_available()
except ImportError:
    EASYOCR_AVAILABLE = False
    GPU_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFProcessor:
    """Centralized PDF processing and text extraction"""
    
    def __init__(self):
        self.setup_dependencies()
    
    def setup_dependencies(self):
        """Check and report available dependencies"""
        self.dependencies = {
            'pymupdf4llm': PYMUPDF4LLM_AVAILABLE,
            'easyocr': EASYOCR_AVAILABLE,
            'gpu': GPU_AVAILABLE,
            'pymupdf': PYMUPDF_AVAILABLE
        }
    
    def get_dependency_status(self) -> Dict[str, bool]:
        """Get status of all dependencies"""
        return self.dependencies.copy()
    
    def evaluate_text_quality(self, text: str) -> bool:
        """
        Evaluate text quality to determine if OCR is needed
        Centralized quality evaluation logic
        """
        if not text or not text.strip():
            return False
        
        # Check text length
        if len(text.strip()) < TEXT_QUALITY['min_chars']:
            return False
        
        # Check for meaningful words
        words = text.split()
        if len(words) < TEXT_QUALITY['min_words']:
            return False
        
        # Check for excessive special characters
        special_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
        if len(text) > 0 and special_chars / len(text) > TEXT_QUALITY['max_special_char_ratio']:
            return False
        
        # Check for reasonable word-to-space ratio
        if text.count(' ') < len(words) * TEXT_QUALITY['min_word_space_ratio']:
            return False
        
        return True
    
    def extract_with_pymupdf4llm(self, pdf_path: str) -> Optional[str]:
        """Extract text using PyMuPDF4LLM for structured output"""
        if not PYMUPDF4LLM_AVAILABLE:
            return None
        
        try:
            text = pymupdf4llm.to_markdown(pdf_path)
            return text if text else None
        except Exception as e:
            st.warning(f"PyMuPDF4LLM extraction failed: {e}")
            return None
    
    def extract_with_easyocr(self, pdf_path: str, use_gpu: Optional[bool] = None, 
                           languages: List[str] = None, min_confidence: float = None) -> Optional[str]:
        """Extract text using EasyOCR for scanned documents"""
        if not EASYOCR_AVAILABLE:
            return None
        
        if not PYMUPDF_AVAILABLE:
            st.error("PyMuPDF required for PDF to image conversion")
            return None
        
        # Set defaults
        if use_gpu is None:
            use_gpu = GPU_AVAILABLE
        if languages is None:
            languages = OCR_CONFIG['default_languages']
        if min_confidence is None:
            min_confidence = OCR_CONFIG['min_confidence']
        
        try:
            # GPU status reporting
            if use_gpu and GPU_AVAILABLE:
                pass
            elif use_gpu and not GPU_AVAILABLE:
                st.warning("⚠️ GPU requested but not available, using CPU")
                use_gpu = False
            else:
                pass
            
            # Initialize EasyOCR reader
            reader = easyocr.Reader(languages, gpu=use_gpu)
            
            # Convert PDF to images using PyMuPDF
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                st.warning("⚠️ PDF appears to be empty")
                doc.close()
                return None
            
            extracted_text = ""
            
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    
                    # Convert page to image with high resolution
                    mat = fitz.Matrix(2.0, 2.0)  # 144 DPI
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to numpy array
                    img_data = pix.tobytes("png")
                    img_array = np.frombuffer(img_data, dtype=np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    if img is None:
                        continue
                    
                    # Preprocess image for better OCR
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    thresh = cv2.adaptiveThreshold(
                        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                    )
                    
                    # Apply noise reduction
                    kernel = np.ones((1, 1), np.uint8)
                    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                    
                    # Extract text with EasyOCR
                    results = reader.readtext(thresh, detail=1, paragraph=False)
                    results.sort(key=lambda x: x[0][0][1])  # Sort by y-coordinate
                    
                    page_text = ""
                    for (bbox, text, confidence) in results:
                        text = text.strip()
                        if text and confidence >= min_confidence:
                            page_text += text + " "
                    
                    if page_text.strip():
                        extracted_text += page_text + "\n"
                        
                except Exception as page_error:
                    st.warning(f"⚠️ Failed to process page {page_num + 1}: {page_error}")
                    continue
            
            doc.close()
            
            # Clean up text
            extracted_text = ' '.join(extracted_text.split())
            
            if not extracted_text.strip():
                st.warning("⚠️ EasyOCR could not extract meaningful text")
                return None
            
            return extracted_text
            
        except Exception as e:
            st.error(f"❌ EasyOCR extraction failed: {e}")
            return None
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Get basic PDF information"""
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(pdf_path)
                info = {
                    'pages': len(doc),
                    'metadata': doc.metadata,
                    'is_encrypted': doc.needs_pass,
                    'has_text': False
                }
                
                # Check if PDF has extractable text
                sample_text = ""
                for i in range(min(2, len(doc))):
                    sample_text += doc[i].get_text()
                
                info['has_text'] = len(sample_text.strip()) > 50
                doc.close()
                return info
            else:
                return {'pages': 1, 'metadata': {}, 'is_encrypted': False, 'has_text': True}
                
        except Exception as e:
            st.warning(f"Could not get PDF info: {e}")
            return {'pages': 1, 'metadata': {}, 'is_encrypted': False, 'has_text': True}
    
    def extract_text_hybrid(self, pdf_path: str, development_mode: bool = False) -> str:
        """
        Main text extraction method using hybrid approach
        PyMuPDF4LLM → EasyOCR with intelligent fallback
        """
        if development_mode:
            return self._extract_development_mode(pdf_path)

        
        # Tier 1: Try PyMuPDF4LLM (structured output)
        text = self.extract_with_pymupdf4llm(pdf_path)
        if text and self.evaluate_text_quality(text):
            return text
        
        # Tier 2: Use EasyOCR for scanned documents
        if EASYOCR_AVAILABLE:
            st.warning("Document appears to be scanned. Using OCR...")
            with st.spinner("🔄 Processing with OCR..."):
                text = self.extract_with_easyocr(pdf_path)
                if text and text.strip():
                    return text
        else:
            st.error("OCR not available. Install: pip install easyocr opencv-python torch")
        
        # Fallback
        st.error("Text extraction failed")
        return "Error: Unable to extract text from the document."
    
    def _extract_development_mode(self, pdf_path: str) -> str:
        """Development mode with detailed comparison"""        
        # GPU settings
        col_gpu1, col_gpu2 = st.columns(2)
        with col_gpu1:
            if GPU_AVAILABLE:
                use_gpu = st.checkbox("Use GPU for EasyOCR", value=True)
                gpu_info = torch.cuda.get_device_name(0)
                st.success(f"GPU Detected: {gpu_info}")
            else:
                st.warning("No GPU detected - using CPU")
                use_gpu = False
        
        with col_gpu2:
            if not GPU_AVAILABLE:
                st.info("""
                **To enable GPU acceleration:**
                1. **Uninstall CPU PyTorch:**
                   ```
                   pip uninstall torch torchvision torchaudio
                   ```
                2. **Install CUDA PyTorch:**
                   ```
                   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
                   ```
                3. **Restart the app**
                """)
            else:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                st.info(f"GPU Memory: {gpu_memory:.1f} GB")
        
        # Create comparison columns
        col1, col2 = st.columns(2)
        results = {}
        
        # Test PyMuPDF4LLM
        with col1:
            st.subheader("PyMuPDF4LLM (Structured)")
            if PYMUPDF4LLM_AVAILABLE:
                start_time = time.time()
                text = self.extract_with_pymupdf4llm(pdf_path)
                processing_time = time.time() - start_time
                
                if text:
                    quality = self.evaluate_text_quality(text)
                    chars = len(text)
                    words = len(text.split())
                    
                    results['pymupdf4llm'] = {
                        'text': text,
                        'time': processing_time,
                        'quality': quality,
                        'chars': chars,
                        'words': words
                    }
                    
                    st.success(f"Extracted in {processing_time:.2f}s")
                    st.metric("Characters", f"{chars:,}")
                    st.metric("Words", f"{words:,}")
                    st.metric("Quality Check", "PASSED" if quality else "FAILED")
                    
                    with st.expander("Preview (500 chars)"):
                        st.code(text[:500] + "..." if len(text) > 500 else text, language="markdown")
                    
                    st.download_button(
                        label="Download PyMuPDF4LLM Text",
                        data=text,
                        file_name="resume_pymupdf4llm.md",
                        mime="text/markdown"
                    )
                else:
                    st.error("No text extracted")
                    results['pymupdf4llm'] = None
            else:
                st.warning("PyMuPDF4LLM not available")
                results['pymupdf4llm'] = None
        
        # Test EasyOCR
        with col2:
            st.subheader("EasyOCR (Optical)")
            if EASYOCR_AVAILABLE:
                start_time = time.time()
                with st.spinner("Processing with OCR..."):
                    text = self.extract_with_easyocr(pdf_path, use_gpu=use_gpu)
                processing_time = time.time() - start_time
                
                if text:
                    quality = self.evaluate_text_quality(text)
                    chars = len(text)
                    words = len(text.split())
                    
                    results['easyocr'] = {
                        'text': text,
                        'time': processing_time,
                        'quality': quality,
                        'chars': chars,
                        'words': words
                    }
                    
                    st.success(f"Extracted in {processing_time:.2f}s")
                    st.metric("Characters", f"{chars:,}")
                    st.metric("Words", f"{words:,}")
                    st.metric("Quality Check", "PASSED" if quality else "FAILED")
                    
                    with st.expander("Preview (500 chars)"):
                        st.text(text[:500] + "..." if len(text) > 500 else text)
                    
                    st.download_button(
                        label="Download EasyOCR Text",
                        data=text,
                        file_name="resume_easyocr.txt",
                        mime="text/plain"
                    )
                else:
                    st.warning("No text extracted")
                    results['easyocr'] = None
            else:
                st.warning("EasyOCR not available")
                results['easyocr'] = None
        
        # Comparison summary
        self._display_comparison_summary(results)
        
        # Return best result
        return self._select_best_result(results)
    
    def _display_comparison_summary(self, results: Dict[str, Any]):
        """Display comparison summary table"""
        st.subheader("Comparison Summary")
        
        comparison_data = []
        for method_name, method_data in results.items():
            if method_data:
                comparison_data.append({
                    'Method': method_name.replace('pymupdf4llm', 'PyMuPDF4LLM').replace('easyocr', 'EasyOCR'),
                    'Time (s)': f"{method_data['time']:.2f}",
                    'Characters': f"{method_data['chars']:,}",
                    'Words': f"{method_data['words']:,}",
                    'Quality': "PASSED" if method_data['quality'] else "FAILED"
                })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)
            
            if len(comparison_data) > 1:
                fastest = min(comparison_data, key=lambda x: float(x['Time (s)']))
                longest_text = max(comparison_data, key=lambda x: int(x['Characters'].replace(',', '')))
                
                st.info(f"Fastest: {fastest['Method']} ({fastest['Time (s)']}s)")
                st.info(f"Most Text: {longest_text['Method']} ({longest_text['Characters']} chars)")
    
    def _select_best_result(self, results: Dict[str, Any]) -> str:
        """Select the best extraction result"""
        st.subheader("Method Selection")
        
        if results.get('pymupdf4llm') and results['pymupdf4llm']['quality']:
            st.success("PyMuPDF4LLM selected (best structured output)")
            return results['pymupdf4llm']['text']
        elif results.get('easyocr') and results['easyocr']['quality']:
            st.warning("EasyOCR selected (fallback for scanned documents)")
            return results['easyocr']['text']
        else:
            st.error("No method produced quality results")
            return "Error: Unable to extract text from the document."


# Global PDF processor instance
pdf_processor = PDFProcessor() 