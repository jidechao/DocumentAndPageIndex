# Custom Model Support Specification

## ADDED Requirements

### Requirement: Support OPENAI_BASE_URL Environment Variable
The system SHALL read and support the `OPENAI_BASE_URL` environment variable for configuring custom OpenAI-compatible API endpoints.

#### Scenario: User sets custom base URL via environment variable
Given the user has set `OPENAI_BASE_URL=https://api.example.com/v1` in their environment
When the system initializes an OpenAI client
Then the client SHALL be configured to use `https://api.example.com/v1` as the base URL

#### Scenario: Custom base URL with trailing slash
Given the user has set `OPENAI_BASE_URL=https://api.example.com/v1/` in their environment
When the system initializes an OpenAI client
Then the client SHALL handle the trailing slash appropriately without causing double slashes in API paths

### Requirement: Maintain Default OpenAI Endpoint Behavior
The system SHALL maintain existing functionality when no custom base URL is provided, using OpenAI's default endpoint.

#### Scenario: No custom base URL configured
Given the user has not set `OPENAI_BASE_URL` in their environment
When the system initializes an OpenAI client
Then the client SHALL use OpenAI's default base URL
And all existing functionality SHALL work unchanged

#### Scenario: Existing configuration without base URL
Given the user has existing configuration with only `CHATGPT_API_KEY` set
When the system starts
Then it SHALL operate exactly as before
And no warnings or errors SHALL be generated about missing base URL

### Requirement: Enhanced OpenAI Client Initialization
OpenAI client initialization SHALL support optional base URL parameter while maintaining existing function signatures.

#### Scenario: Synchronous API client with custom base URL
Given a custom base URL is configured
When calling `ChatGPT_API()` function
Then the OpenAI client SHALL be initialized with the custom base URL
And the function SHALL return results from the custom endpoint

#### Scenario: Asynchronous API client with custom base URL
Given a custom base URL is configured
When calling `ChatGPT_API_async()` function
Then the AsyncOpenAI client SHALL be initialized with the custom base URL
And the function SHALL return results from the custom endpoint

### Requirement: Base URL Validation
The system SHALL perform basic validation on provided base URLs and provide appropriate error messages for invalid URLs.

#### Scenario: Invalid URL format
Given the user sets `OPENAI_BASE_URL=not-a-valid-url` in their environment
When the system attempts to initialize the OpenAI client
Then it SHALL provide a clear error message indicating the URL format is invalid

#### Scenario: Valid URL but unreachable endpoint
Given the user sets `OPENAI_BASE_URL=https://unreachable-api.example.com/v1` in their environment
When the system attempts to make API calls
Then it SHALL provide appropriate connection error messages
And the error handling SHALL be consistent with existing OpenAI client behavior

### Requirement: Graceful Error Handling for Custom Endpoints
Error handling for custom endpoints SHALL be consistent with existing OpenAI API error handling patterns.

#### Scenario: Authentication failure with custom endpoint
Given a custom base URL is configured
When the API key is invalid for the custom endpoint
Then the system SHALL handle authentication errors appropriately
And error messages SHALL be consistent with existing behavior

#### Scenario: Model not found on custom endpoint
Given a custom base URL is configured
When the requested model is not available on that endpoint
Then the system SHALL provide appropriate error messages
And error handling SHALL be consistent with existing behavior

### Requirement: Environment Variable Precedence
Environment variables SHALL take precedence over any default values when configuring the base URL.

#### Scenario: Both environment variable and config file specify base URL
Given `OPENAI_BASE_URL` is set in environment
And a different base URL is specified in config.yaml
When the system initializes the OpenAI client
Then the environment variable value SHALL be used
And a warning SHOULD be logged about the configuration conflict

## MODIFIED Requirements

### Requirement: Update ChatGPT_API Function
The `ChatGPT_API()` function SHALL be modified to support custom base URLs while maintaining backward compatibility.

#### Scenario: Function signature compatibility
Given existing code calls `ChatGPT_API()` with current parameters
When the function is called
Then it SHALL work exactly as before
And no breaking changes SHALL be introduced to the function signature

#### Scenario: Base URL parameter passing
Given a custom base URL needs to be passed explicitly
When calling the function
Then it SHALL accept the base URL parameter
And use it when provided

### Requirement: Update ChatGPT_API_async Function
The `ChatGPT_API_async()` function SHALL be modified to support custom base URLs while maintaining backward compatibility.

#### Scenario: Async function signature compatibility
Given existing code calls `ChatGPT_API_async()` with current parameters
When the function is called
Then it SHALL work exactly as before
And no breaking changes SHALL be introduced to the function signature

#### Scenario: Async base URL usage
Given a custom base URL is configured
When making async API calls
Then all async operations SHALL use the custom base URL
And performance SHALL be equivalent to default configuration

### Requirement: Enhanced ConfigLoader
The ConfigLoader class SHALL be updated to handle base URL configuration if extended to support config file settings.

#### Scenario: Config file with base URL
Given a config.yaml file includes a base_url setting
When the configuration is loaded
Then it SHALL properly parse and validate the base URL
And provide it through the configuration interface

#### Scenario: Mixed configuration sources
Given base URL is specified in both environment variables and config file
When the configuration is loaded
Then environment variable SHALL take precedence
And appropriate warnings SHALL be logged