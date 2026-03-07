# 🛡️ Shared Core — LicensePanel Ecosystem

Common infrastructure, security, and logic layer for the AlphaLicense and Infrastructure ecosystem. This library centralizes database management, authentication, and core utilities to ensure consistency across all backend modules.

## 🚀 Overview

`shared-core` provides high-level abstractions for:
- 🗄️ **Database Factory**: Centralized connection pooling for MySQL, PostgreSQL, SQLite, and Turso (LibSQL).
- 🔑 **Security & Auth**: JWT management, Password hashing (Argon2), and API Key validation.
- 📡 **MQTT Integration**: Standardized messaging for regional synchronization.
- ⚙️ **Config Management**: Pydantic-based settings with environment variable support.

## 🛠️ Usage & Installation

### Local Development
To link this library during development so changes are reflected in real-time:
```bash
# From ApiLicense or Infrastructure/Core
pip install -e ./shared_core
```

### Production (Hugging Face / Docker)
The library is installed directly from the private GitHub repository using a secure token:
```dockerfile
RUN --mount=type=secret,id=GH_TOKEN \
    export TOKEN=$(cat /run/secrets/GH_TOKEN) && \
    pip install git+https://oauth2:${TOKEN}@github.com/ItsWatuyusei/shared-core.git
```

## 🗃️ Database Configuration

When using **Turso (LibSQL)**, ensure your `DATABASE_URL` uses the correct SQLAlchemy dialect prefix:

- **Correct:** `libsql+libsql://your-db-url.turso.io`
- **Incorrect:** `libsql://your-db-url.turso.io`

### Required Dependencies
Ensure the following are in your project's `requirements.txt`:
```text
libsql-client>=0.3.0
libsql>=0.1.0
sqlalchemy-libsql==0.1.0
```

## 🔐 Security Constants

All sub-projects must define the following in their `.env`:
- `CSRF_SECRET`: Base entropy for internal encryption.
- `MASTER_ENCRYPTION_KEY`: 256-bit key for sensitive data storage.
- `GH_TOKEN`: GitHub Personal Access Token for library installation.

---
*Developed by ItsWatuyusei Suite Engine Team*
