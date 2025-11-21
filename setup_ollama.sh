#!/bin/bash
# ============================================================================
# Ollama Local LLM Setup Script for CESAR.ai
# ============================================================================
# Purpose: Automate installation and configuration of local Ollama models
# Models: Qwen 2.5 Coder 7B, Llama 3 8B
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# Check Prerequisites
# ============================================================================

check_ollama_installed() {
    if command -v ollama &> /dev/null; then
        print_success "Ollama is installed"
        OLLAMA_VERSION=$(ollama --version 2>&1 | head -n 1)
        print_info "Version: $OLLAMA_VERSION"
        return 0
    else
        print_warning "Ollama is not installed"
        return 1
    fi
}

check_ollama_running() {
    if curl -s http://localhost:11434/api/version &> /dev/null; then
        print_success "Ollama server is running"
        return 0
    else
        print_warning "Ollama server is not running"
        return 1
    fi
}

check_model_installed() {
    local model_name=$1
    if ollama list | grep -q "$model_name"; then
        print_success "Model '$model_name' is installed"
        return 0
    else
        print_warning "Model '$model_name' is not installed"
        return 1
    fi
}

# ============================================================================
# Installation Functions
# ============================================================================

install_ollama() {
    print_header "Installing Ollama"

    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            print_info "Installing via Homebrew..."
            brew install ollama
            print_success "Ollama installed via Homebrew"
        else
            print_info "Downloading macOS installer..."
            curl -fsSL https://ollama.ai/install.sh | sh
            print_success "Ollama installed"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_info "Installing on Linux..."
        curl -fsSL https://ollama.ai/install.sh | sh
        print_success "Ollama installed"
    else
        print_error "Unsupported OS: $OSTYPE"
        print_info "Please install manually from https://ollama.ai"
        exit 1
    fi
}

start_ollama_server() {
    print_header "Starting Ollama Server"

    if check_ollama_running; then
        return 0
    fi

    print_info "Starting Ollama server in background..."

    # Start server in background
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use launchd if available
        if command -v launchctl &> /dev/null; then
            brew services start ollama 2>/dev/null || ollama serve &> /dev/null &
        else
            ollama serve &> /dev/null &
        fi
    else
        # Linux - start as background process
        nohup ollama serve &> /tmp/ollama.log &
    fi

    # Wait for server to start
    print_info "Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/version &> /dev/null; then
            print_success "Ollama server is running on http://localhost:11434"
            return 0
        fi
        sleep 1
    done

    print_error "Failed to start Ollama server"
    return 1
}

pull_model() {
    local model_name=$1
    local display_name=$2

    print_header "Downloading $display_name"

    if check_model_installed "$model_name"; then
        print_info "Model already installed, checking for updates..."
    else
        print_info "Downloading model (this may take several minutes)..."
    fi

    if ollama pull "$model_name"; then
        print_success "Model '$model_name' is ready"

        # Get model info
        local model_size=$(ollama list | grep "$model_name" | awk '{print $2}')
        print_info "Size: $model_size"
        return 0
    else
        print_error "Failed to download model '$model_name'"
        return 1
    fi
}

test_model() {
    local model_name=$1
    local display_name=$2

    print_header "Testing $display_name"

    print_info "Running test query..."
    local test_response=$(ollama run "$model_name" "Say 'Hello from CESAR.ai!' in one short sentence." 2>&1)

    if [ $? -eq 0 ]; then
        print_success "Model test successful!"
        print_info "Response: $test_response"
        return 0
    else
        print_error "Model test failed"
        return 1
    fi
}

# ============================================================================
# Database Migration
# ============================================================================

run_migration() {
    print_header "Applying Database Migration"

    # Check if migration file exists
    if [ ! -f "migrations/007_local_llm_integration.sql" ]; then
        print_error "Migration file not found: migrations/007_local_llm_integration.sql"
        return 1
    fi

    # Database connection details
    DB_HOST="${POSTGRES_HOST:-localhost}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    DB_NAME="${POSTGRES_DB:-mcp}"
    DB_USER="${POSTGRES_USER:-mcp_user}"

    print_info "Connecting to database: $DB_HOST:$DB_PORT/$DB_NAME"

    # Check if psql is available
    if ! command -v psql &> /dev/null; then
        print_warning "psql not found. Please run migration manually:"
        print_info "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f migrations/007_local_llm_integration.sql"
        return 1
    fi

    # Run migration
    if PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migrations/007_local_llm_integration.sql; then
        print_success "Database migration applied successfully"
        return 0
    else
        print_error "Database migration failed"
        return 1
    fi
}

# ============================================================================
# Main Setup Flow
# ============================================================================

main() {
    print_header "CESAR.ai Local LLM Setup (Ollama)"

    echo ""
    print_info "This script will:"
    print_info "  1. Install Ollama (if not installed)"
    print_info "  2. Start Ollama server"
    print_info "  3. Download Qwen 2.5 Coder 7B (~4.7 GB)"
    print_info "  4. Download Llama 3 8B (~4.7 GB)"
    print_info "  5. Test both models"
    print_info "  6. Apply database migration"
    echo ""

    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Setup cancelled"
        exit 0
    fi

    echo ""

    # Step 1: Check/Install Ollama
    if ! check_ollama_installed; then
        install_ollama
    fi

    # Step 2: Start Server
    start_ollama_server || exit 1

    # Step 3: Download Models
    pull_model "qwen2.5-coder:7b" "Qwen 2.5 Coder 7B" || exit 1
    pull_model "llama3:8b" "Llama 3 8B" || exit 1

    # Step 4: Test Models
    test_model "qwen2.5-coder:7b" "Qwen 2.5 Coder 7B"
    test_model "llama3:8b" "Llama 3 8B"

    # Step 5: Apply Migration
    if [ -f ".env" ] || [ -n "$POSTGRES_PASSWORD" ]; then
        run_migration
    else
        print_warning "Database credentials not found in .env"
        print_info "Skipping migration. Run manually when ready:"
        print_info "  psql -h localhost -U mcp_user -d mcp -f migrations/007_local_llm_integration.sql"
    fi

    # Final Summary
    echo ""
    print_header "Setup Complete! 🎉"
    echo ""
    print_success "Ollama is running on http://localhost:11434"
    print_success "Models installed:"
    ollama list
    echo ""
    print_info "Next steps:"
    print_info "  1. Restart your CESAR.ai API server to use new models"
    print_info "  2. Local models will be used for:"
    print_info "     - Development and testing tasks (free)"
    print_info "     - Privacy-sensitive data (stays local)"
    print_info "     - Offline work (no internet needed)"
    print_info "  3. Cloud models will still be used for:"
    print_info "     - Production workloads (higher quality)"
    print_info "     - Complex reasoning tasks"
    print_info "     - Vision and multimodal tasks"
    echo ""
    print_info "View routing strategy:"
    print_info "  SELECT * FROM llm_deployment_strategy;"
    echo ""
}

# ============================================================================
# Run Main
# ============================================================================

main "$@"
