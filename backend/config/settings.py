# General system settings

# Telegram settings
TELEGRAM = {
    "MAX_FILE_SIZE_MB": 20,
    "SUPPORTED_FILE_TYPES": [".pdf", ".docx", ".txt", ".md", ".html"],
    "MAX_CONCURRENT_PROCESSES": 3,
    "COMMANDS": {
        "START": "/start",
        "HELP": "/help",
        "ADD": "/add",
        "SEARCH": "/search",
        "STATUS": "/status",
        "SESSION": "/session", 
    },
}

# Document processing settings
DOCUMENT_PROCESSING = {
    "CHUNK_SIZE": 200,
    "CHUNK_OVERLAP": 20,
    "TEMP_DIR": "temp_uploads",
}

# Indexing settings
INDEXING = {
    "INDEX_NAME": "Knowledge Base",
    "EMBEDDING_MODEL": "673248d66eb563b2b00f75d1",  
}

# Security settings
SECURITY = {
    "AUTHORIZED_USER_IDS": [], 
    "MAX_MESSAGE_LENGTH": 4000,
}
