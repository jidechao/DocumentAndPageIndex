# Add Custom Model Support with Base URL Configuration

## Why

Currently, PageIndex is hardcoded to use OpenAI's official API endpoint, preventing users from leveraging self-hosted models, alternative providers, or custom deployments while maintaining the same functionality.

## What Changes

- Add `OPENAI_BASE_URL` environment variable support for custom OpenAI-compatible APIs
- Update OpenAI client initialization to use custom base URL when provided
- Maintain backward compatibility with existing configurations
- Update configuration validation to handle base URL settings
- Add error handling for invalid base URLs

## Impact

- **Affected specs**: custom-model-support (new capability)
- **Affected code**: `pageindex/utils.py` (OpenAI client initialization functions)
- **Configuration**: New optional environment variable with validation