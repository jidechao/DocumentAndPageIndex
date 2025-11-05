# Custom Model Support - Design Document

## Architecture Overview

This design extends the existing OpenAI client initialization to support custom base URLs while maintaining full backward compatibility.

## Current Architecture

### Existing Model Client Structure
```python
# pageindex/utils.py (current implementation)
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")

def ChatGPT_API(model, prompt, api_key=CHATGPT_API_KEY, chat_history=None):
    client = openai.OpenAI(api_key=api_key)
    # ... rest of implementation
```

### Configuration Flow
1. `.env` file loaded by `python-dotenv`
2. `CHATGPT_API_KEY` read from environment
3. OpenAI client initialized with default base URL
4. API calls made to OpenAI's standard endpoint

## Proposed Architecture

### Enhanced Model Client Structure
```python
# pageindex/utils.py (proposed changes)
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

def ChatGPT_API(model, prompt, api_key=CHATGPT_API_KEY, base_url=OPENAI_BASE_URL, chat_history=None):
    client_config = {"api_key": api_key}
    if base_url:
        client_config["base_url"] = base_url
    client = openai.OpenAI(**client_config)
    # ... rest of implementation
```

### Updated Configuration Flow
1. `.env` file loaded by `python-dotenv`
2. `CHATGPT_API_KEY` read from environment (existing)
3. `OPENAI_BASE_URL` read from environment (new, optional)
4. OpenAI client initialized with custom base URL if provided
5. API calls made to configured endpoint

## Implementation Details

### 1. Environment Variable Handling
- **New Variable**: `OPENAI_BASE_URL` (optional)
- **Default Behavior**: When not set, uses OpenAI's default endpoint
- **Validation**: Basic URL format validation
- **Priority**: Environment variable takes precedence over defaults

### 2. Client Initialization Strategy
- **Backward Compatibility**: Existing function signatures maintained
- **Default Parameters**: New `base_url` parameter with `None` default
- **Conditional Logic**: Only include `base_url` in client config when provided
- **Error Handling**: Graceful fallback for invalid URLs

### 3. Configuration Integration
- **Config File Support**: Optional extension to config.yaml
- **Validation**: Enhanced ConfigLoader to handle base_url
- **Environment Override**: Environment variables take precedence over config files

## Technical Considerations

### OpenAI Client Compatibility
- The OpenAI Python library natively supports custom base URLs
- No changes needed to API call structure
- All existing functionality preserved

### Error Handling Strategy
- **Invalid URLs**: Clear error messages during client initialization
- **Connection Failures**: Standard OpenAI client error handling
- **Authentication**: Existing API key validation applies

### Performance Implications
- **Client Creation**: Minimal overhead from additional configuration
- **API Calls**: No impact on request/response handling
- **Memory Usage**: Negligible increase from additional configuration

## Security Considerations

### API Key Management
- No changes to existing API key handling
- API keys still required for custom endpoints
- Environment variable security best practices maintained

### URL Validation
- Basic format validation to prevent injection
- HTTPS preference for secure connections
- No execution of dynamic content from URLs

## Migration Path

### For Existing Users
- **No Action Required**: Existing configurations continue to work
- **Optional Enhancement**: Can add base URL for custom models
- **Gradual Adoption**: Users can migrate at their own pace

### For New Users
- **Enhanced Flexibility**: Immediate access to custom model support
- **Clear Documentation**: Setup instructions for various providers
- **Example Configurations**: Templates for common scenarios

## Testing Strategy

### Unit Tests
- Client initialization with and without base URL
- URL validation logic
- Backward compatibility verification

### Integration Tests
- API calls to mock custom endpoints
- Error handling for invalid configurations
- End-to-end functionality verification

### Manual Testing
- Real-world usage with popular custom model providers
- Configuration validation across different environments
- Performance comparison with default configuration

## Future Extensions

### Potential Enhancements
1. **Multiple Provider Support**: Configuration for different providers
2. **Model-Specific URLs**: Different base URLs per model
3. **Load Balancing**: Multiple endpoint support with failover
4. **Authentication Extensions**: Support for different auth methods

### Extensibility Considerations
- Current design allows for easy extension
- Configuration system can accommodate additional parameters
- Client initialization pattern can be reused for new features

## Dependencies and Constraints

### External Dependencies
- **OpenAI Python Library**: Already supports custom base URLs
- **python-dotenv**: Already in use for environment management
- **PyYAML**: Already in use for configuration management

### Project Constraints
- **No Breaking Changes**: Maintain existing API compatibility
- **Minimal Complexity**: Keep implementation simple and focused
- **Performance**: No degradation in API call performance
- **Security**: Maintain existing security practices