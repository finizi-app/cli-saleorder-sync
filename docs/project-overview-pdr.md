# Product Development Requirements (PDR)
## Odoo POS to B4B Sale Order Sync CLI

## Executive Summary

**Product Name:** Odoo POS to B4B Sale Order Sync CLI
**Repository:** finizi-app/cli-saleorder-sync
**Status:** Initial Implementation
**Version:** 0.1.0
**Last Updated:** 2026-03-13

A Python-based CLI tool that enables seamless synchronization of POS sale orders from Odoo ERP to B4B API system with tax-aware pricing and VNPayQR invoice generation capabilities. The tool provides a robust, production-ready solution for businesses needing to integrate their Odoo POS operations with B4B accounting/invoicing systems.

## Vision & Mission

### Vision
To become the de-facto standard for B2B sync solutions between Vietnamese ERP systems, enabling seamless data flow between Odoo POS and B4B accounting platforms.

### Mission
Provide a reliable, secure, and easy-to-use CLI tool that automates the synchronization of POS sale orders while maintaining data integrity and supporting complex tax requirements specific to the Vietnamese market.

## User Personas

### Primary Users
1. **System Administrator**: Responsible for setting up and maintaining the sync tool
2. **Accounting Staff**: Uses the tool to ensure accurate financial data flow
3. **IT Operations Team**: Monitors sync operations and troubleshoots issues

### Secondary Users
1. **Business Owners**: Need to understand sync status and data flow
2. **Auditors**: Require data traceability and audit trails

## Functional Requirements

### FR1: Odoo POS Order Export
- **FR1.1**: Export POS orders from Odoo via XML-RPC API
- **FR1.2**: Support date-based order filtering (YYYY-MM-DD format)
- **FR1.3**: Support timezone-aware date conversion (ICT to UTC)
- **FR1.4**: Filter orders by state (draft, paid, done, invoiced, cancel)
- **FR1.5**: Filter orders by payment method (e.g., VNPayQR, Cash)
- **FR1.6**: Support multiple output formats: JSON, JSONL, CSV
- **FR1.7**: Include comprehensive order data: lines, payments, customer info

### FR2: B4B API Integration
- **FR2.1**: Import formatted orders to B4B REST API
- **FR2.2**: Support JWT Bearer token authentication
- **FR2.3**: Handle entity-based order creation
- **FR2.4**: Provide dry-run mode for testing and validation
- **FR2.5**: Implement batch order processing with configurable limits
- **FR2.6**: Support existing order skipping (deduplication)
- **FR2.7**: Provide detailed import logging and error tracking

### FR3: Tax-Aware Pricing Mapping
- **FR3.1**: Convert Odoo order pricing to B4B tax-aware format
- **FR3.2**: Calculate VAT rates from pre-tax and inclusive prices
- **FR3.3**: Support explicit tax fields: `unit_price_without_tax`, `unit_price_with_tax`, `vat_rate`
- **FR3.4**: Maintain backward compatibility with legacy pricing format
- **FR3.5**: Handle product code/name parsing from Odoo format

### FR4: VNPayQR Invoice Generation
- **FR4.1**: Generate VNPayQR invoices for POS orders
- **FR4.2**: Support POS-specific invoice type
- **FR4.3**: Handle invoice generation errors gracefully
- **FR4.4**: Provide option to skip invoice generation
- **FR4.5**: Maintain invoice generation logs

### FR5: Error Handling & Logging
- **FR5.1**: Handle network connection errors with retries
- **FR5.2**: Provide detailed error messages with timestamps
- **FR5.3**: Implement comprehensive logging (JSONL format)
- **FR5.4**: Support configurable logging levels (DEBUG, INFO, ERROR)
- **FR5.5**: Handle XML-RPC authentication failures
- **FR5.6**: Handle API rate limits and timeouts
- **FR5.7**: Provide audit trail for all operations

## Non-Functional Requirements

### NFR1: Performance & Scalability
- **NFR1.1**: Process 1000+ orders per minute
- **NFR1.2**: Support batch processing with configurable limits
- **NFR1.3**: Handle concurrent operations safely
- **NFR1.4**: Memory efficiency for large order datasets

### NFR2: Reliability & Availability
- **NFR2.1**: 99.9% uptime for sync operations
- **NFR2.2**: Automatic retry mechanism for transient failures
- **NFR2.3**: Data integrity verification during sync
- **NFR2.4**: Graceful degradation during partial failures

### NFR3: Security
- **NFR3.1**: Secure credential handling (environment variables)
- **NFR3.2**: HTTPS connections for all API communications
- **NFR3.3**: Input validation and sanitization
- **NFR3.4**: Secure error message handling (no sensitive data exposure)

### NFR4: Usability
- **NFR4.1**: Intuitive CLI interface with clear help text
- **NFR4.2**: Comprehensive examples and documentation
- **NFR4.3**: Detailed progress indicators during long operations
- **NFR4.4**: Easy configuration via environment variables
- **NFR4.5**: Clear error messages with actionable guidance

### NFR5: Maintainability
- **NFR5.1**: Modular code structure for easy extension
- **NFR5.2**: Comprehensive unit tests (80%+ coverage)
- **NFR5.3**: Code formatting consistency (Black, Ruff)
- **NFR5.4**: Type hints throughout the codebase
- **NFR5.5**: Clear separation of concerns between modules

### NFR6: Compliance
- **NFR6.1**: Support Vietnamese tax regulations (VAT)
- **NFR6.2**: Maintain data privacy standards
- **NFR6.3**: Provide audit trail for all operations
- **NFR6.4**: Handle timezone requirements correctly (ICT)

## Technical Requirements

### TR1: Technology Stack
- **TR1.1**: Python 3.10+ runtime
- **TR1.2**: XML-RPC client for Odoo communication
- **TR1.3**: HTTPX for B4B REST API communication
- **TR1.4**: Pytz for timezone handling
- **TR1.5**: Type hints throughout codebase
- **TR1.6**: Logging with configurable levels

### TR2: API Integration
- **TR2.1**: Odoo XML-RPC API v2
- **TR2.2**: B4B REST API v1 with entity-based endpoints
- **TR2.3**: JWT token-based authentication
- **TR2.4**: JSON request/response format
- **TR2.5**: Proper HTTP status code handling

### TR3: Data Architecture
- **TR3.1**: Use dataclasses for type-safe models
- **TR3.2**: Implement proper serialization/deserialization
- **TR3.3**: Handle null/None values gracefully
- **TR3.4**: Maintain data conversion mappings
- **TR3.5**: Support Vietnamese locale (VND currency, ICT timezone)

### TR4: Error Handling Architecture
- **TR4.1**: Custom exception types for different error scenarios
- **TR4.2**: Retry mechanism with exponential backoff
- **TR4.3**: Proper error logging with context
- **TR4.4**: Graceful degradation for partial failures
- **TR4.5**: User-friendly error messages

## Success Metrics

### Usage Metrics
- **UM1**: Monthly active users: 50+ organizations
- **UM2**: Average orders processed per month: 10,000+
- **UM3**: Sync success rate: 99.5%+
- **UM4**: Average sync duration: < 5 minutes for 1000 orders

### Quality Metrics
- **QM1**: Bug rate: < 1 per 1000 operations
- **QM2**: Critical downtime: < 1 hour per quarter
- **QM3**: User satisfaction: 4.5/5 stars
- **QM4**: Documentation completeness: 95%+

### Business Metrics
- **BM1**: Time saved in manual data entry: 20+ hours per month
- **BM2**: Data accuracy improvement: 99.9%+
- **BM3**: Customer satisfaction with financial reporting
- **BM4**: Reduced operational costs for B2B sync

## Project Phases

### Phase 1: Foundation (Completed)
- ✅ Core Odoo XML-RPC integration
- ✅ Basic POS order export functionality
- ✅ Simple B4B API integration
- ✅ Basic CLI interface

### Phase 2: Enhanced Features (In Progress)
- 🔄 Tax-aware pricing mapping
- 🔄 VNPayQR invoice generation
- 🔄 Advanced filtering and logging
- 🔄 Comprehensive error handling

### Phase 3: Production Ready (Planned)
- 📋 Performance optimization
- 📋 Enhanced security features
- 📋 Monitoring and alerting
- 📋 Comprehensive documentation

### Phase 4: Enterprise Features (Future)
- 📌 Multi-entity support
- 📌 Advanced reporting
- 📌 Web interface for monitoring
- 📌 Integration with other systems

## Risks & Mitigation

### Technical Risks
- **Risk**: Odoo API changes breaking functionality
  - **Mitigation**: Version pinning, thorough testing
- **Risk**: B4B API rate limiting
  - **Mitigation**: Batch processing with backoff
- **Risk**: Data corruption during sync
  - **Mitigation**: Data validation, rollback capability

### Business Risks
- **Risk**: User adoption challenges
  - **Mitigation**: Comprehensive onboarding and support
- **Risk**: Competition from other sync solutions
  - **Mitigation**: Focus on Vietnamese market specific requirements

## Dependencies & Constraints

### External Dependencies
- Odoo 14+ (XML-RPC API support)
- B4B API v1 endpoint
- Python 3.10+ runtime
- Network connectivity to both systems

### Technical Constraints
- CLI-only interface (no GUI in v1)
- Single-threaded processing
- File-based logging
- Environment variable configuration

## Support & Maintenance

### Support Channels
- Email support for enterprise customers
- Documentation and FAQ
- Community forum for open-source users

### Maintenance Schedule
- Regular security patches: Monthly
- Feature updates: Quarterly
- Major version releases: Bi-annually
- Documentation updates: Continuous

## Future Roadmap

### Version 0.2.0 (Planned)
- Multi-file batch processing
- Advanced filtering capabilities
- Performance monitoring
- Enhanced error reporting

### Version 1.0.0 (Target)
- Enterprise-grade reliability
- Advanced security features
- Web dashboard for monitoring
- Integration with notification systems

### Version 2.0.0 (Future)
- Multi-entity support
- Cloud-hosted service option
- Advanced analytics and reporting
- Integration with other Vietnamese ERP systems

---

*This PDR document will be updated as the project evolves and new requirements are identified.*