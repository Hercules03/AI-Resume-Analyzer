# OpenAI Integration Setup Guide

This guide will help you set up OpenAI API integration with the AI Resume Analyzer.

## 🚀 Quick Setup

### 1. Install Required Dependencies

```bash
pip install langchain-openai openai
```

### 2. Get Your OpenAI API Key

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign in to your OpenAI account
3. Click "Create new secret key"
4. Copy your API key (it starts with `sk-`)

### 3. Set Environment Variable

#### Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=sk-your-actual-api-key-here
```

#### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
```

#### Linux/Mac:
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

#### Permanent Setup (Windows):
1. Search for "Environment Variables" in Start Menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables" button
4. Click "New" under User variables
5. Variable name: `OPENAI_API_KEY`
6. Variable value: `sk-your-actual-api-key-here`

#### Permanent Setup (Linux/Mac):
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export OPENAI_API_KEY="sk-your-actual-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Alternative: Configure in Code (Not Recommended)

You can also set your API key directly in `App/config.py`:

```python
# OpenAI Configuration
'openai': {
    'default_model': 'gpt-4o-mini',
    'temperature': 0.1,
    'max_tokens': 4096,
    'top_p': 0.9,
    'timeout': 60,
    'api_key': 'sk-your-actual-api-key-here'  # Add your key here
}
```

⚠️ **Security Warning**: Don't commit API keys to version control!

## 🎛️ Using the System

1. **Start the Application**:
   ```bash
   cd App
   streamlit run pages/evaluation.py
   ```

2. **Select Provider**: In the web interface, choose "openai" from the LLM Provider dropdown

3. **Choose Model**: Select your preferred OpenAI model:
   - `gpt-4o` - Latest and most capable
   - `gpt-4o-mini` - Cost-effective, good performance
   - `gpt-4-turbo` - High performance
   - `gpt-3.5-turbo` - Fastest and most economical

4. **Check Connection**: Look for the green ✅ Connected status

## 💰 Cost Considerations

### Recommended Models by Use Case:

- **High Volume Processing**: `gpt-4o-mini` (~$0.15 per 1M input tokens)
- **Best Quality**: `gpt-4o` (~$2.50 per 1M input tokens)
- **Balanced**: `gpt-4-turbo` (~$10 per 1M input tokens)

### Typical Resume Processing Costs:
- **gpt-4o-mini**: ~$0.01-0.03 per resume
- **gpt-4o**: ~$0.05-0.15 per resume
- **gpt-4-turbo**: ~$0.20-0.60 per resume

## 🔧 Configuration Options

You can customize OpenAI settings in `App/config.py`:

```python
'openai': {
    'default_model': 'gpt-4o-mini',     # Change default model
    'temperature': 0.1,                  # 0.0 = deterministic, 1.0 = creative
    'max_tokens': 4096,                  # Maximum response length
    'top_p': 0.9,                        # Nucleus sampling
    'timeout': 60,                       # Request timeout in seconds
    'api_key': None                      # Use environment variable
}
```

## 🆚 Ollama vs OpenAI Comparison

| Feature | Ollama (Local) | OpenAI (Cloud) |
|---------|----------------|----------------|
| **Cost** | Free (after setup) | Pay per use |
| **Privacy** | 100% local | Data sent to OpenAI |
| **Speed** | Depends on hardware | Usually faster |
| **Quality** | Good (varies by model) | Excellent |
| **Setup** | More complex | Simple |
| **Reliability** | Depends on hardware | High |

## 🔍 Troubleshooting

### "OpenAI API key not found"
- Verify your environment variable is set correctly
- Restart your terminal/IDE after setting the variable
- Check for typos in the variable name

### "OpenAI not available"
- Install dependencies: `pip install langchain-openai openai`
- Restart the application

### "Rate limit exceeded"
- You've hit OpenAI's rate limits
- Wait a few minutes or upgrade your OpenAI plan
- Consider switching to a local Ollama model temporarily

### "Invalid API key"
- Double-check your API key is correct
- Ensure it starts with `sk-`
- Regenerate the key if needed

## 🛡️ Security Best Practices

1. **Never commit API keys to code repositories**
2. **Use environment variables**
3. **Rotate API keys regularly**
4. **Monitor your OpenAI usage dashboard**
5. **Set up billing alerts in OpenAI dashboard**

## 📞 Support

If you encounter issues:
1. Check the connection status in the web interface
2. Verify your API key in the OpenAI dashboard
3. Try switching between models
4. Check the debug mode for detailed error messages 