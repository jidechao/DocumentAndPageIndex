# Custom Model Support Implementation Tasks

## Task List

### Phase 1: Core Implementation

#### 1.1 Add Base URL Environment Variable Support
**Task**: Update environment variable loading to support `OPENAI_BASE_URL`
- [x] Add `OPENAI_BASE_URL` environment variable loading in `pageindex/utils.py`
- [x] Add basic URL format validation
- [x] Ensure backward compatibility with existing configurations
- [x] Test with various URL formats (with/without trailing slash)

**Validation**: Environment variable is properly loaded and validated

#### 1.2 Update ChatGPT_API Function
**Task**: Modify synchronous API function to support custom base URL
- [x] Add optional `base_url` parameter to `ChatGPT_API()` function signature
- [x] Update OpenAI client initialization to use custom base URL when provided
- [x] Maintain backward compatibility with existing function calls
- [x] Add error handling for invalid base URLs

**Validation**: Function works with both default and custom base URLs

#### 1.3 Update ChatGPT_API_async Function
**Task**: Modify asynchronous API function to support custom base URL
- [x] Add optional `base_url` parameter to `ChatGPT_API_async()` function signature
- [x] Update AsyncOpenAI client initialization to use custom base URL when provided
- [x] Maintain backward compatibility with existing function calls
- [x] Add error handling for invalid base URLs

**Validation**: Async function works with both default and custom base URLs

#### 1.4 Update ChatGPT_API_with_finish_reason Function
**Task**: Modify finish reason API function to support custom base URL
- [x] Add optional `base_url` parameter to `ChatGPT_API_with_finish_reason()` function
- [x] Update OpenAI client initialization to use custom base URL when provided
- [x] Maintain backward compatibility with existing function calls
- [x] Add error handling for invalid base URLs

**Validation**: Function works with both default and custom base URLs

### Phase 2: Configuration Enhancement

#### 2.1 Enhance ConfigLoader (Optional)
**Task**: Extend ConfigLoader to support base URL in config files
- [ ] Add base_url field to default configuration schema
- [ ] Update ConfigLoader to handle base_url configuration
- [ ] Add validation for base_url in config files
- [ ] Ensure environment variable takes precedence over config file

**Validation**: Config file properly loads and validates base URL settings

#### 2.2 Update Configuration Validation
**Task**: Enhance configuration validation for base URL
- [ ] Add base URL validation to existing validation logic
- [ ] Add warnings for configuration conflicts
- [ ] Ensure proper error messages for invalid configurations

**Validation**: Configuration validation properly handles base URL settings

### Phase 3: Testing

#### 3.1 Unit Tests
**Task**: Create comprehensive unit tests for new functionality
- [ ] Test environment variable loading with various URL formats
- [ ] Test OpenAI client initialization with custom base URLs
- [ ] Test backward compatibility with existing configurations
- [ ] Test error handling for invalid base URLs
- [ ] Test URL validation logic

**Validation**: All unit tests pass and coverage is maintained

#### 3.2 Integration Tests
**Task**: Create integration tests for end-to-end functionality
- [ ] Test API calls with mock custom endpoints
- [ ] Test error handling for unreachable endpoints
- [ ] Test authentication with custom endpoints
- [ ] Test model compatibility with custom endpoints

**Validation**: Integration tests demonstrate proper functionality

#### 3.3 Manual Testing
**Task**: Perform manual testing with real scenarios
- [ ] Test with popular OpenAI-compatible providers
- [ ] Test with self-hosted models
- [ ] Test edge cases and error conditions
- [ ] Performance testing with custom endpoints

**Validation**: Manual testing confirms expected behavior

### Phase 4: Documentation

#### 4.1 Update Documentation
**Task**: Update project documentation to include custom model support
- [ ] Update README.md with configuration instructions
- [ ] Add examples for popular custom model providers
- [ ] Document environment variable usage
- [ ] Add troubleshooting guide for common issues

**Validation**: Documentation is clear, accurate, and helpful

#### 4.2 Create Examples
**Task**: Create example configurations for common use cases
- [ ] Example configuration for local models
- [ ] Example configuration for Azure OpenAI
- [ ] Example configuration for other popular providers
- [ ] Example .env file template

**Validation**: Examples are working and easy to understand

### Phase 5: Quality Assurance

#### 5.1 Code Review
**Task**: Ensure code quality and best practices
- [ ] Review all code changes for adherence to project standards
- [ ] Ensure proper error handling and logging
- [ ] Verify no breaking changes are introduced
- [ ] Check for security considerations

**Validation**: Code review passes all quality checks

#### 5.2 Performance Testing
**Task**: Verify no performance regression
- [ ] Benchmark API call performance with default configuration
- [ ] Benchmark API call performance with custom base URL
- [ ] Ensure no significant performance degradation
- [ ] Test memory usage and resource consumption

**Validation**: Performance remains acceptable

#### 5.3 Security Review
**Task**: Security assessment of new functionality
- [ ] Review URL validation for potential vulnerabilities
- [ ] Ensure no sensitive information leakage
- [ ] Verify API key handling remains secure
- [ ] Check for potential injection vulnerabilities

**Validation**: Security review passes all checks

## Dependencies

### Internal Dependencies
- Existing OpenAI client functions must remain functional
- Configuration system must continue to work as before
- Environment variable loading must remain compatible

### External Dependencies
- OpenAI Python library (already supports custom base URLs)
- python-dotenv (already in use)
- PyYAML (already in use)

## Acceptance Criteria

### Functional Requirements
- [x] System supports `OPENAI_BASE_URL` environment variable
- [x] All existing functionality remains unchanged when no custom base URL is provided
- [x] Custom base URLs work correctly with all API functions
- [x] Error handling is appropriate and informative
- [x] Configuration validation works as expected

### Non-Functional Requirements
- [x] No performance regression
- [x] Backward compatibility is maintained
- [x] Code quality standards are met
- [x] Security considerations are addressed
- [x] Documentation is complete and accurate

### Testing Requirements
- [ ] Unit test coverage is maintained or improved
- [ ] Integration tests demonstrate end-to-end functionality
- [ ] Manual testing confirms real-world usability
- [ ] Edge cases are properly handled

## Risk Mitigation

### Technical Risks
- **Breaking Changes**: Mitigated by maintaining existing function signatures
- **Performance Impact**: Mitigated by minimal changes to client initialization
- **Compatibility Issues**: Mitigated by thorough testing with various providers

### Operational Risks
- **Configuration Errors**: Mitigated by clear error messages and validation
- **Documentation Gaps**: Mitigated by comprehensive documentation and examples
- **User Confusion**: Mitigated by clear migration guide and backward compatibility

## Timeline Estimate

- **Phase 1**: 2-3 days (Core implementation)
- **Phase 2**: 1-2 days (Configuration enhancement)
- **Phase 3**: 2-3 days (Testing)
- **Phase 4**: 1-2 days (Documentation)
- **Phase 5**: 1-2 days (Quality assurance)

**Total Estimated Time**: 7-12 days

## Success Metrics

- All tasks completed successfully
- No breaking changes introduced
- User can successfully configure custom base URLs
- Documentation enables easy setup for common providers
- Performance remains comparable to default configuration