# System Architecture
## Odoo POS to B4B Sale Order Sync CLI

## Overview

The Odoo POS to B4B Sale Order Sync CLI follows a modular, layered architecture that separates concerns between external system integration, data processing, and user interface layers. This design ensures maintainability, testability, and scalability while handling the complexities of Vietnamese market tax requirements and B2B synchronization.

## Architecture Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        A[CLI Interface] --> B[Odoo Export CLI]
        A --> C[B4B Import CLI]
        D[Configuration] --> E[Environment Variables]
        D --> F[CLI Arguments]
    end

    subgraph "Application Layer"
        B --> G[Odoo Integration]
        C --> H[B4B Integration]
        I[Data Mapping] --> J[Tax-Aware Pricing]
        I --> K[Order Transformation]
    end

    subgraph "Data Processing Layer"
        G --> L[Data Models]
        H --> L
        J --> L
        K --> L
        M[Output Formatters] --> L
    end

    subgraph "Infrastructure Layer"
        N[Timezone Utilities] --> O[ICT/UTC Conversion]
        P[Error Handling] --> Q[Retry Mechanism]
        P --> R[Logging System]
        S[Configuration Management] --> T[Credential Handling]
    end

    subgraph "External Systems"
        U[Odoo Server] --> V[XML-RPC API]
        W[B4B Platform] --> X[REST API]
        Y[Network] --> V
        Y --> X
    end

    B --> V
    C --> X
    G --> V
    H --> X
```

## Component Architecture

### 1. CLI Layer
**Purpose**: Provide user interface and command-line interaction

**Components**:
- **Odoo Export CLI (`src/cli.py`)**: Handles order export from Odoo
- **B4B Import CLI (`src/b4b_import_cli.py`)**: Handles order import to B4B
- **Configuration Management**: Supports both CLI args and environment variables

**Key Features**:
- Argument parsing with comprehensive options
- Environment variable fallback
- Progress indication and error reporting
- Multiple output format support

### 2. Integration Layer
**Purpose**: Handle communication with external systems

**Components**:
- **Odoo XML-RPC Client (`src/client.py`)**:
  - XML-RPC API communication
  - Authentication and session management
  - Retry mechanism with exponential backoff
  - Error handling and logging

- **B4B REST API Client (`src/b4b_client.py`)**:
  - HTTP-based REST API communication
  - JWT token authentication
  - Context manager for resource cleanup
  - Proper HTTP status code handling

### 3. Data Processing Layer
**Purpose**: Transform and process order data between systems

**Components**:
- **Data Models (`src/models.py`)**:
  - Type-safe dataclasses for POS orders
  - Product line and payment models
  - Serialization and deserialization methods

- **Order Mapper (`src/order_mapper.py`)**:
  - Tax-aware pricing calculations
  - Odoo to B4B field mapping
  - VAT rate calculations
  - Status and date transformations

- **Output Formatters (`src/formatters.py`)**:
  - JSON, JSONL, CSV output formats
  - Metadata calculation
  - CSV escaping and formatting

### 4. Utilities Layer
**Purpose**: Provide supporting functionality for the application

**Components**:
- **Timezone Utilities (`src/timezone_utils.py`)**:
  - ICT to UTC conversion for Odoo queries
  - Date range calculations
  - ISO datetime formatting

- **Error Handling System**:
  - Custom exception hierarchy
  - Retry mechanisms
  - Comprehensive logging
  - Graceful degradation

- **Configuration Management**:
  - Environment variable handling
  - Credential management
  - Validation and fallback logic

## Data Flow Architecture

### Primary Sync Flow

```mermaid
sequenceDiagram
    participant User
    participant OdooCLI
    participant OdooClient
    participant OdooAPI
    participant Importer
    participant Mapper
    participant B4BClient
    participant B4BAPI

    User->>OdooCLI: Export orders --date 2026-03-11
    OdooCLI->>OdooClient: Connect(url, db, user, pass)
    OdooClient->>OdooAPI: Authenticate
    OdooAPI->>OdooClient: User ID + Session

    OdooCLI->>Importer: import_orders(date, timezone)
    Importer->>OdooAPI: Search orders by date range
    OdooAPI->>Importer: Order records
    Importer->>OdooAPI: Fetch lines & payments
    OdooAPI->>Importer: Complete order data

    Importer->>Mapper: map_orders(odoo_orders)
    Mapper->>Mapper: tax_calculations()
    Mapper->>B4BClient: create_sale_order(b4b_orders)

    B4BClient->>B4BAPI: JWT Authentication
    B4BAPI->>B4BClient: Auth Token

    B4BClient->>B4BAPI: POST /sale-orders
    B4BAPI->>B4BClient: Order Created (201)
    B4BClient->>B4BAPI: POST /generate-vnpay-invoice
    B4BAPI->>B4BClient: Invoice Generated (200)

    B4BClient->>User: Import Summary
```

### Tax-Aware Data Transformation

```mermaid
graph LR
    A[Odoo Order] --> B[Order Mapper]
    B --> C[Tax Calculations]
    B --> D[Field Mapping]
    B --> E[Status Transformation]

    C --> F[VAT Rate Calculation]
    C --> G[Price Separation]
    C --> H[Tax-Inclusive/Exclusive Pricing]

    D --> I[B4B Compatible Fields]
    E --> J[B4B Status Codes]

    F --> K[decimal vat_rate]
    G --> L[unit_price_without_tax]
    G --> M[unit_price_with_tax]

    H --> N[Auto-calculated by B4B]
    I --> O[B4B Sale Order Format]
    J --> P[B4B Status System]

    O --> Q[Ready for B4B API]
```

## Error Handling Architecture

### Error Types and Handling

```mermaid
graph TB
    subgraph "Exception Hierarchy"
        A[SyncError] --> B[OdooConnectionError]
        A --> C[B4BApiError]
        A --> D[ValidationError]
        A --> E[ConfigurationError]
    end

    subgraph "Error Handling Flow"
        F[Network Error] --> G[Retry Mechanism]
        H[Auth Failure] --> I[Clear Error Message]
        J[Data Validation] --> K[Helpful Guidance]
        L[Rate Limiting] --> M[Exponential Backoff]
    end

    subgraph "Logging Strategy"
        N[Error Events] --> O[Structured Logging]
        P[Success Events] --> Q[Progress Tracking]
        R[Debug Events] --> S[Verbose Logging]
    end

    G --> H
    H --> I
    K --> L
    M --> N
    O --> P
    P --> Q
```

## Performance Architecture

### Batch Processing Pattern

```mermaid
graph TB
    A[Large Order Set] --> B[Batch Size: 100]
    B --> C[Process Batch 1]
    B --> D[Process Batch 2]
    B --> E[Process Batch 3]

    C --> F[B4B API Call]
    D --> F
    E --> F

    F --> G[Response Handling]
    G --> H[Success/Failure Tracking]
    H --> I[Next Batch]

    I --> J{All Processed?}
    J -->|No| B
    J -->|Yes| K[Generate Report]
```

### Memory Management Strategy

```mermaid
graph LR
    A[Order Data] --> B[Streaming Processing]
    B --> C[Lazy Loading]
    C --> D[Generator Pattern]
    D --> E[Memory Efficient]

    F[XML-RPC] --> G[Batch Fetching]
    G --> H[Cached Objects]
    H --> I[Reused Connections]

    J[HTTP Client] --> K[Connection Pooling]
    K --> L[Resource Cleanup]
    L --> M[Context Managers]
```

## Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Input Validation"
        A[User Input] --> B[Type Checking]
        B --> C[Range Validation]
        C --> D[Format Validation]
        D --> E[Sanitization]
    end

    subgraph "Authentication"
        F[Environment Variables] --> G[Credential Storage]
        G --> H[Secure Transmission]
        H --> I[JWT Token Handling]
    end

    subgraph "Network Security"
        J[HTTPS] --> K[Certificate Validation]
        K --> L[Timeout Protection]
        L --> M[Rate Limiting]
    end

    subgraph "Data Protection"
        N[Logging] --> O[Data Masking]
        O --> P[Secure Error Messages]
        P --> Q[No Sensitive Data]
    end

    E --> F
    I --> J
    M --> N
```

## Deployment Architecture

### Local Development Environment

```mermaid
graph TB
    A[Developer Machine] --> B[Python 3.10+]
    B --> C[Virtual Environment]
    C --> D[Source Code]
    D --> E[Dependencies]
    E --> F[Testing Framework]

    F --> G[Local Odoo Instance]
    F --> H[Local B4B API]

    D --> I[CLI Tools]
    I --> J[Debug Mode]
    J --> K[Logging Output]
```

### Production Deployment

```mermaid
graph TB
    subgraph "Production Environment"
        A[Server] --> B[Python Application]
        B --> C[Configuration Management]
        C --> D[Environment Variables]
        D --> E[Secure Storage]

        B --> F[Logging System]
        F --> G[Log Rotation]
        G --> H[Monitoring]

        B --> I[Process Management]
        I --> J[Systemd Service]
        J --> K[Auto-restart]
    end

    subgraph "External Systems"
        L[Odoo Production] --> M[XML-RPC API]
        N[B4B Production] --> O[REST API]

        M --> P[Network Security]
        O --> P
    end

    H --> L
    H --> N
```

## Monitoring and Observability

### Logging Architecture

```mermaid
graph LR
    A[Application Events] --> B[Structured Logging]
    B --> C[JSON Format]
    C --> D[File Output]
    D --> E[Log Rotation]

    F[Error Events] --> G[Error Tracking]
    G --> H[Alert System]

    I[Performance Metrics] --> J[Metrics Collection]
    J --> K[Dashboard]

    D --> L[Audit Trail]
    H --> M[Notifications]
    K --> O[Monitoring]
```

### Health Checks

```mermaid
graph TB
    A[Health Check System] --> B[Odoo Connection]
    A --> C[B4B API]
    A --> D[Database Status]
    A --> E[Network Connectivity]

    B --> F[Response Time]
    C --> F
    D --> G[Data Integrity]
    E --> H[Latency]

    F --> I[Health Status]
    G --> I
    H --> I

    I --> J[Alert System]
```

## Scaling Considerations

### Horizontal Scaling

```mermaid
graph TB
    A[Load Balancer] --> B[Worker 1]
    A --> C[Worker 2]
    A --> D[Worker N]

    B --> E[Order Queue]
    C --> E
    D --> E

    E --> F[B4B API Pool]
    F --> G[Batch Processing]

    G --> H[Result Aggregation]
    H --> I[Response Queue]
    I --> J[Client Response]
```

### Performance Optimization

```mermaid
graph LR
    A[Performance Bottlenecks] --> B[Network Latency]
    A --> C[Memory Usage]
    A --> D[CPU Processing]
    A --> E[I/O Operations]

    B --> F[Connection Pooling]
    C --> G[Streaming Processing]
    D --> H[Parallel Processing]
    E --> I[Async Operations]

    F --> J[Optimized Pipeline]
    G --> J
    H --> J
    I --> J
```

## Technology Stack

### Core Technologies
- **Python 3.10+**: Runtime environment
- **Type Hints**: Static type checking
- **Dataclasses**: Type-safe data structures
- **XML-RPC Client**: Odoo communication
- **HTTPX**: B4B API communication
- **Pytz**: Timezone handling

### Development Tools
- **Black**: Code formatting
- **Ruff**: Linting and formatting
- **Pytest**: Testing framework
- **Mypy**: Type checking
- **Git**: Version control

### External Dependencies
- **Odoo 14+**: XML-RPC API server
- **B4B Platform**: REST API endpoint
- **Network**: HTTPS connectivity
- **Storage**: File system for logging

---

*This architecture documentation provides a comprehensive overview of the system's design and implementation. The architecture is designed to be flexible, maintainable, and scalable while addressing the specific requirements of Vietnamese market POS-to-B4B synchronization.*