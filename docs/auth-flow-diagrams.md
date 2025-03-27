# Authentication Flow Diagrams

This document contains the flow diagrams for the Cognito authentication system implemented in the Experimentation Platform.

## 1. Registration and Confirmation Flow

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant API as API Server
    participant Cognito as AWS Cognito
    participant Email as Email Service

    User->>Client: Enter registration information
    Client->>API: POST /auth/signup
    API->>Cognito: SignUp API call
    Cognito->>Email: Send verification code
    Cognito-->>API: Return UserSub (successful registration)
    API-->>Client: Return success + instructions
    Client-->>User: Show verification required message
    
    User->>Client: Enter verification code
    Client->>API: POST /auth/confirm
    API->>Cognito: ConfirmSignUp API call
    Cognito-->>API: Confirm success
    API-->>Client: Account confirmed
    Client-->>User: Show registration complete
```

## 2. Sign-in and Token Issuance Flow

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant API as API Server
    participant Cognito as AWS Cognito
    
    User->>Client: Enter credentials
    Client->>API: POST /auth/token
    API->>Cognito: InitiateAuth API call
    
    alt Successful Authentication
        Cognito-->>API: Return tokens (Access, ID, Refresh)
        API-->>Client: Return tokens + metadata
        Client->>Client: Store tokens securely
        Client-->>User: Redirect to dashboard/home
    else Authentication Challenge
        Cognito-->>API: Return challenge (MFA, new password required)
        API-->>Client: Return challenge details
        Client-->>User: Show challenge UI
        User->>Client: Complete challenge
        Client->>API: POST /auth/challenge
        API->>Cognito: RespondToAuthChallenge API call
        Cognito-->>API: Return tokens
        API-->>Client: Return tokens + metadata
        Client->>Client: Store tokens securely
        Client-->>User: Redirect to dashboard/home
    else Failed Authentication
        Cognito-->>API: Authentication error
        API-->>Client: Return error message
        Client-->>User: Show error message
    end
```

## 3. Password Reset Flow

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant API as API Server
    participant Cognito as AWS Cognito
    participant Email as Email Service
    
    User->>Client: Request password reset
    Client->>API: POST /auth/forgot-password
    API->>Cognito: ForgotPassword API call
    Cognito->>Email: Send reset code
    Cognito-->>API: Reset code sent
    API-->>Client: Success message
    Client-->>User: Show code entry UI
    
    User->>Client: Enter code + new password
    Client->>API: POST /auth/reset-password
    API->>Cognito: ConfirmForgotPassword API call
    
    alt Successful Reset
        Cognito-->>API: Password updated
        API-->>Client: Success message
        Client-->>User: Show login prompt
    else Invalid Code
        Cognito-->>API: Code invalid/expired
        API-->>Client: Error message
        Client-->>User: Show error, prompt to try again
    else Password Policy Failure
        Cognito-->>API: Password doesn't meet requirements
        API-->>Client: Password policy error
        Client-->>User: Show password requirements
    end
```

## 4. Token Refresh Mechanism

```mermaid
sequenceDiagram
    participant Client
    participant API as API Server
    participant Cognito as AWS Cognito
    
    Note over Client: Access token expires
    Client->>Client: Detect expired token
    Client->>API: POST /auth/refresh (with refresh token)
    API->>Cognito: InitiateAuth (REFRESH_TOKEN flow)
    
    alt Successful Refresh
        Cognito-->>API: New access & ID tokens
        API-->>Client: Return new tokens
        Client->>Client: Update stored tokens
    else Expired Refresh Token
        Cognito-->>API: Token expired error
        API-->>Client: Authentication required
        Client->>Client: Clear stored tokens
        Client->>Client: Redirect to login
    else Invalid Token
        Cognito-->>API: Invalid token error
        API-->>Client: Authentication required
        Client->>Client: Clear stored tokens
        Client->>Client: Redirect to login
    end
```

## 5. Authorization Decision Flow

```mermaid
flowchart TD
    A[Request to protected endpoint] --> B{Has Authorization header?}
    B -->|Yes| C{Extract token}
    B -->|No| D[Return 401 Unauthorized]
    
    C -->|Success| E{Validate token}
    C -->|Failure| D
    
    E -->|Valid| F{Check token expiration}
    E -->|Invalid| D
    
    F -->|Not expired| G{Check permissions/roles}
    F -->|Expired| H{Has refresh token?}
    
    G -->|Has permission| I[Process request]
    G -->|No permission| J[Return 403 Forbidden]
    
    H -->|Yes| K[Attempt token refresh]
    H -->|No| D
    
    K -->|Success| E
    K -->|Failure| D
```

## 6. Error Handling Flow

```mermaid
flowchart TD
    A[Authentication error occurs] --> B{Error type?}
    
    B -->|Invalid credentials| C[Return 401 - Wrong username/password]
    B -->|User not confirmed| D[Return 400 - Account not verified]
    B -->|Password reset required| E[Return 401 - Password reset required]
    B -->|Invalid token| F[Return 401 - Invalid token]
    B -->|Expired token| G[Return 401 - Token expired]
    B -->|Invalid code| H[Return 400 - Invalid verification code]
    B -->|Code expired| I[Return 400 - Verification code expired]
    B -->|User not found| J[Return 404 - User not found]
    B -->|Internal error| K[Return 500 - Internal server error]
    
    C --> L[Log authentication failure]
    D --> M[Log unconfirmed account attempt]
    E --> N[Log password reset needed]
    F --> O[Log invalid token]
    G --> P[Log expired token]
    H --> Q[Log invalid code]
    I --> R[Log expired code]
    J --> S[Log user not found]
    K --> T[Log internal error details]
    
    L --> U[Return appropriate error response to client]
    M --> U
    N --> U
    O --> U
    P --> U
    Q --> U
    R --> U
    S --> U
    T --> U
```

These diagrams provide a comprehensive visual documentation of the authentication flows in the system. They can be used for developer reference, onboarding, and architectural documentation.
