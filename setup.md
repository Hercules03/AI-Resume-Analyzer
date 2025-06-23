# 🚀 AI Resume Analyzer - Complete Setup Guide

This comprehensive guide covers all aspects of setting up the AI Resume Analyzer, from basic installation to advanced GPU acceleration and LLM configuration.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Setup](#detailed-setup)
- [LLM Setup (Ollama)](#llm-setup-ollama)
- [GPU Acceleration](#gpu-acceleration)
- [Database Configuration](#database-configuration)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)
- [Advanced Configuration](#advanced-configuration)

## 🔧 System Requirements

### **Minimum Requirements**
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8+ (3.9.12 recommended)
- **RAM**: 8GB system memory
- **Storage**: 5GB free space for dependencies and models
- **Internet**: Required for initial setup and model downloads

### **Recommended for Optimal Performance**
- **OS**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Python**: 3.9+ with pip 21+
- **RAM**: 16GB+ (especially for LLM features)
- **GPU**: RTX 5090, RTX 4090, RTX 3090, or equivalent
- **Storage**: SSD with 10GB+ free space
- **Network**: Stable internet for initial model downloads

### **Additional Software**
- **MySQL**: For database functionality
- **Visual Studio Code**: Recommended code editor
- **Visual Studio Build Tools**: For C++ dependencies (Windows)

## ⚡ Quick Installation

### **1. Clone Repository**
```bash
git clone <your-repository-url>
cd AI-Resume-Analyzer
```

### **2. Create Virtual Environment** (Recommended)
```bash
# Create virtual environment
python -m venv venvapp

# Activate virtual environment
# Windows:
venvapp\Scripts\activate
# macOS/Linux:
source venvapp/bin/activate
```

### **3. Install Dependencies**
```bash
cd App
pip install -r requirements.txt
```

### **4. Install Language Model**
```bash
python -m spacy download en_core_web_sm
```

### **5. Run Application**
```bash
streamlit run App.py
```

## 📖 Detailed Setup

### **Step 1: Python Environment Setup**

#### **Install Python 3.9.12** (Recommended)
- **Windows**: Download from [python.org](https://www.python.org/downloads/release/python-3912/)
- **macOS**: `brew install python@3.9`
- **Ubuntu**: `sudo apt update && sudo apt install python3.9 python3.9-pip`

#### **Verify Installation**
```bash
python --version  # Should show Python 3.9.12 or similar
pip --version     # Should show pip 21.0+
```

### **Step 2: Project Setup**

#### **Clone and Navigate**
```bash
git clone <your-repository-url>
cd AI-Resume-Analyzer
```

#### **Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venvapp

# Activate (keep this activated for all following commands)
# Windows Command Prompt:
venvapp\Scripts\activate

# Windows PowerShell:
venvapp\Scripts\Activate.ps1

# macOS/Linux:
source venvapp/bin/activate
```

### **Step 3: Install Core Dependencies**

#### **Navigate to App Directory**
```bash
cd App
```

#### **Install Python Packages**
```bash
pip install -r requirements.txt
```

#### **Install SpaCy Language Model**
```bash
python -m spacy download en_core_web_sm
```

## 🤖 LLM Setup (Ollama)

### **Install Ollama**

#### **Windows**
```bash
# Option 1: Download installer
# Visit: https://ollama.ai/download/windows

# Option 2: Use winget
winget install Ollama.Ollama
```

#### **macOS**
```bash
# Option 1: Download from https://ollama.ai/download/mac
# Option 2: Use Homebrew
brew install ollama
```

#### **Linux**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### **Pull Required Models**

#### **Start Ollama Service**
```bash
# Start Ollama (keep this running in a separate terminal)
ollama serve
```

#### **Download Models** (In another terminal)
```bash
# Primary model (recommended)
ollama pull gemma2:27b

# Alternative models for different performance needs
ollama pull gemma2:9b      # Faster, smaller
ollama pull llama3.1:8b    # Good balance
ollama pull mistral:7b     # Lightweight
ollama pull qwen2.5:14b    # High accuracy
```

### **Model Selection Guide**

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `gemma2:27b` | ~16GB | Slower | Highest | Production, detailed analysis |
| `gemma2:9b` | ~5GB | Fast | High | Balanced performance |
| `llama3.1:8b` | ~4.7GB | Fast | Good | Quick processing |
| `mistral:7b` | ~4GB | Very Fast | Moderate | Development/testing |

## 🎮 GPU Acceleration

### **RTX 5090 and Modern GPUs**

The RTX 5090 requires special PyTorch installation due to its cutting-edge CUDA architecture (`sm_120`).

#### **Uninstall Existing PyTorch**
```bash
pip uninstall torch torchvision torchaudio -y
```

#### **Install PyTorch Nightly (Required for RTX 5090)**
```bash
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

#### **Verify GPU Installation**
```bash
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('GPU name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU'); print('GPU memory:', round(torch.cuda.get_device_properties(0).total_memory/1024**3, 1), 'GB' if torch.cuda.is_available() else ''); print('CUDA capability:', torch.cuda.get_device_capability(0) if torch.cuda.is_available() else 'N/A')"
```

**Expected Output for RTX 5090:**
```
PyTorch version: 2.8.0.dev20250621+cu128
CUDA available: True
GPU name: NVIDIA GeForce RTX 5090
GPU memory: 31.8 GB
CUDA capability: (12, 0)
```

### **Other GPU Models**

#### **RTX 4090, RTX 4080, RTX 3090, etc.**
```bash
# Standard PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### **CPU-Only Installation**
```bash
# If no GPU or experiencing issues
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### **Additional GPU Dependencies**

#### **Install pdf2image Dependencies**

**Windows:**
```bash
# Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
# Extract and add to PATH, or use conda:
conda install poppler
```

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

## 🗄️ Database Configuration

### **Install MySQL**

#### **Download and Install**
- **All Platforms**: [MySQL Downloads](https://www.mysql.com/downloads/)
- **Ubuntu**: `sudo apt install mysql-server`
- **macOS**: `brew install mysql`

### **Database Setup**

#### **Default Configuration**
The application uses these default settings:
```
Host: localhost
User: root
Password: @dmin1234
Database: cv (auto-created)
```

#### **Custom Database Configuration**
If you need different credentials, modify `App/App.py`:
```python
connection = pymysql.connect(
    host='your_host',
    user='your_username',
    password='your_password',
    db='cv'
)
```

#### **Create Database** (Optional - auto-created on first run)
```sql
CREATE DATABASE cv;
```

## 🚀 Running the Application

### **Start Required Services**

#### **1. Start Ollama** (In first terminal)
```bash
ollama serve
```

#### **2. Start MySQL** (If not auto-starting)
```bash
# Windows: Start MySQL service from Services panel
# macOS: brew services start mysql
# Linux: sudo systemctl start mysql
```

#### **3. Activate Virtual Environment** (In second terminal)
```bash
# Navigate to project
cd AI-Resume-Analyzer

# Activate virtual environment
# Windows:
venvapp\Scripts\activate
# macOS/Linux:
source venvapp/bin/activate

# Navigate to App directory
cd App
```

#### **4. Run Application**
```bash
streamlit run App.py
```

### **Access Application**
Open your browser and navigate to: `http://localhost:8501`

## 🎯 Usage Guide

### **Basic Usage**

1. **Enable LLM Features**: Check "Enable LLM Metadata Extraction" in the sidebar
2. **Configure Model**: Select your preferred model (gemma2:27b recommended)
3. **Upload Resume**: Use the file uploader to select a PDF resume
4. **View Results**: Explore the tabbed interface for detailed analysis

### **Development Mode**

Enable "Show LLM Processing Details" to see:
- Extraction method comparison
- Processing times and performance metrics
- GPU utilization information
- Quality assessment details

### **Admin Access**

- **Username**: `admin`
- **Password**: `admin@resume-analyzer`

## 🔧 Troubleshooting

### **Common Installation Issues**

#### **1. Import Errors**
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Verify critical imports
python -c "import streamlit, pandas, pymysql; print('Core dependencies OK')"
```

#### **2. Ollama Connection Issues**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama service
# Kill existing process, then:
ollama serve
```

#### **3. GPU Detection Problems**
```bash
# Verify CUDA installation
nvidia-smi

# Check PyTorch GPU support
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio -y
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

#### **4. PDF Processing Errors**
```bash
# Install additional dependencies
pip install PyMuPDF easyocr pdf2image opencv-python pymupdf4llm

# Install poppler (for pdf2image)
# See GPU Acceleration section for platform-specific instructions
```

#### **5. Database Connection Issues**
```bash
# Check MySQL status
# Windows: Check Services panel
# macOS: brew services list | grep mysql
# Linux: sudo systemctl status mysql

# Test database connection
python -c "import pymysql; print('PyMySQL imported successfully')"
```

### **Performance Issues**

#### **Slow OCR Processing**
- Enable GPU acceleration in the application
- Verify CUDA PyTorch installation
- Check available GPU memory
- Consider using smaller/faster model variants

#### **High Memory Usage**
- Close unnecessary applications
- Use lighter LLM models (gemma2:9b instead of 27b)
- Restart the application periodically
- Monitor GPU memory usage

#### **Model Loading Errors**
```bash
# Re-download models
ollama rm gemma2:27b
ollama pull gemma2:27b

# Check model status
ollama list
```

### **Network and Dependency Issues**

#### **Slow Downloads**
```bash
# Use alternative PyTorch index
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124

# Clear pip cache
pip cache purge
```

#### **Version Conflicts**
```bash
# Create fresh environment
deactivate
rm -rf venvapp
python -m venv venvapp
# Then follow installation steps again
```

## ⚡ Performance Optimization

### **Hardware Optimization**

#### **GPU Acceleration Benefits**
- **EasyOCR**: 3-10x faster processing with RTX 5090
- **Memory Usage**: ~2-4GB GPU memory for typical resumes
- **Processing Time**: Reduced from 30-60s to 3-10s per page

#### **Memory Management**
- **System RAM**: 16GB+ recommended for LLM features
- **GPU Memory**: RTX 5090's 32GB handles multiple concurrent analyses
- **Storage**: SSD recommended for faster model loading

### **Software Optimization**

#### **Model Selection for Speed**
```bash
# For development/testing (fastest)
ollama pull mistral:7b

# For balanced performance
ollama pull gemma2:9b

# For maximum accuracy (slower)
ollama pull gemma2:27b
```

#### **Batch Processing Optimization**
- Process multiple resumes sequentially rather than simultaneously
- Monitor GPU memory usage to avoid out-of-memory errors
- Use development mode to compare extraction methods

### **Configuration Tuning**

#### **EasyOCR Settings**
```python
# In App.py, adjust these parameters:
min_confidence = 0.6  # Lower for more text, higher for accuracy
gpu = True           # Enable GPU acceleration
languages = ['en']   # Specify only needed languages
```

#### **LLM Settings**
- Use appropriate model size for your hardware
- Monitor processing times and adjust model if needed
- Enable development mode to track performance metrics

## 🔄 Updates and Maintenance

### **Keeping Dependencies Updated**

#### **Monthly Updates**
```bash
# Update PyTorch nightly (for RTX 5090)
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128 --upgrade

# Update other packages
pip install -r requirements.txt --upgrade
```

#### **Ollama Model Updates**
```bash
# Check for model updates
ollama list

# Update specific model
ollama pull gemma2:27b
```

### **Backup and Recovery**

#### **Database Backup**
```bash
# Export MySQL database
mysqldump -u root -p cv > backup_cv.sql

# Restore from backup
mysql -u root -p cv < backup_cv.sql
```

#### **Configuration Backup**
- Save your modified `App.py` configurations
- Document any custom database settings
- Keep a record of your preferred model configurations

## 🎯 Next Steps

### **After Successful Installation**

1. **Test Basic Functionality**: Upload a sample resume and verify extraction
2. **Enable LLM Features**: Configure Ollama and test AI-powered analysis
3. **Optimize Performance**: Enable GPU acceleration if available
4. **Explore Features**: Try development mode and admin dashboard
5. **Customize Settings**: Adjust models and thresholds for your use case

### **Production Deployment**

For production environments, consider:
- Setting up dedicated MySQL server
- Configuring reverse proxy (nginx)
- Implementing user authentication
- Setting up automated backups
- Monitoring system performance

### **Development and Customization**

- Explore the codebase structure
- Modify LLM prompts for specific use cases
- Add custom fields to the database schema
- Integrate with existing HR systems
- Contribute improvements back to the project

---

## 🆘 Getting Help

If you encounter issues not covered in this guide:

1. **Check the logs**: Look for error messages in the terminal
2. **Verify dependencies**: Ensure all packages are installed correctly
3. **Test components**: Use the verification commands provided
4. **Review documentation**: Check specific sections for your issue
5. **Community support**: Submit issues on the project repository

---

<div align="center">
  <p><strong>Your AI Resume Analyzer is ready to transform HR workflows! 🚀</strong></p>
</div> 