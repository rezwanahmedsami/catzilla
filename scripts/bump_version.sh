#!/bin/bash
# Catzilla Version Bump Script
# Professional automated version management with validation and testing

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

print_info() {
    echo -e "${BLUE}$1${NC}"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

show_help() {
    cat << EOF
🚀 Catzilla Version Bump Script

Usage: $0 <new_version> [options]

Arguments:
  new_version     New version number (e.g., 0.2.0, 0.2.1b1, 1.0.0rc1)

Options:
  --no-tests      Skip running tests before bump
  --no-commit     Update files but don't commit
  --no-tag        Don't create git tag
  --dry-run       Show what would be done without making changes
  --help, -h      Show this help message

Examples:
  $0 0.1.1                    # Patch release
  $0 0.2.0                    # Minor release
  $0 1.0.0                    # Major release
  $0 0.2.1b1                  # Beta release
  $0 1.0.0rc1                 # Release candidate
  $0 0.1.1 --no-tests         # Skip tests
  $0 0.2.0 --dry-run          # Preview changes

Semantic Versioning:
  MAJOR.MINOR.PATCH
  Optional prerelease suffixes use PEP 440 format: aN, bN, rcN
EOF
}

NEW_VERSION=""
RUN_TESTS=true
DO_COMMIT=true
DO_TAG=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-tests)
            RUN_TESTS=false
            shift
            ;;
        --no-commit)
            DO_COMMIT=false
            shift
            ;;
        --no-tag)
            DO_TAG=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            if [[ -z "$NEW_VERSION" ]]; then
                NEW_VERSION="$1"
            else
                print_error "Unknown argument: $1"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$NEW_VERSION" ]]; then
    print_error "❌ Error: Version number is required"
    echo ""
    show_help
    exit 1
fi

if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+((a|b|rc)[0-9]+)?$ ]]; then
    print_error "❌ Invalid version format: $NEW_VERSION"
    print_error "   Expected format: MAJOR.MINOR.PATCH or PEP 440 pre-release (e.g., 0.2.0, 0.2.1b1, 1.0.0rc1)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif [[ -x "$PROJECT_ROOT/venv/bin/python" ]]; then
    PYTHON_CMD="$PROJECT_ROOT/venv/bin/python"
else
    PYTHON_CMD="python3"
fi

RELEASE_FILES=(
    "CMakeLists.txt"
    "pyproject.toml"
    "setup.py"
    "python/catzilla/__init__.py"
    "scripts/version.py"
    "scripts/bump_version.sh"
)

print_header "🚀 Catzilla Version Bump to $NEW_VERSION"
print_info "📁 Project root: $PROJECT_ROOT"
print_info "🐍 Python: $PYTHON_CMD"

if [[ "$DRY_RUN" == "true" ]]; then
    print_warning "🔍 DRY RUN MODE - No changes will be made"
fi

cd "$PROJECT_ROOT"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "❌ Not in a git repository"
    exit 1
fi

CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"

if [[ -n $(git status --porcelain) ]]; then
    print_warning "⚠️  Warning: You have uncommitted changes"
    git status --short
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Aborted by user"
        exit 1
    fi
fi

print_status "📋 Current version status:"
"$PYTHON_CMD" scripts/version.py --check || print_warning "⚠️  Version inconsistencies detected - will be fixed during update"

if git tag -l | grep -q "^v$NEW_VERSION$"; then
    print_error "❌ Tag v$NEW_VERSION already exists"
    exit 1
fi

if [[ "$RUN_TESTS" == "true" ]]; then
    print_status "🧪 Running tests to ensure stability..."

    if [[ "$DRY_RUN" == "false" ]]; then
        if [[ -f "scripts/run_tests.sh" ]]; then
            chmod +x scripts/run_tests.sh
            if ! ./scripts/run_tests.sh; then
                print_error "❌ Tests failed! Aborting version bump."
                print_info "💡 Fix tests or use --no-tests flag to skip"
                exit 1
            fi
        else
            print_warning "⚠️  No test script found, running basic import test..."
            if ! "$PYTHON_CMD" -c "import catzilla; print(f'✅ Catzilla {catzilla.__version__} imported successfully')"; then
                print_error "❌ Basic import test failed!"
                exit 1
            fi
        fi
        print_status "✅ All tests passed!"
    else
        print_info "   [DRY RUN] Would run: ./scripts/run_tests.sh"
    fi
else
    print_warning "⚠️  Skipping tests (--no-tests flag used)"
fi

print_status "📝 Updating version in all files..."

if [[ "$DRY_RUN" == "false" ]]; then
    if ! "$PYTHON_CMD" scripts/version.py "$NEW_VERSION"; then
        print_error "❌ Failed to update version files"
        exit 1
    fi
else
    print_info "   [DRY RUN] Would run: $PYTHON_CMD scripts/version.py $NEW_VERSION"
fi

print_status "🔍 Verifying version consistency..."
if [[ "$DRY_RUN" == "false" ]]; then
    if ! "$PYTHON_CMD" scripts/version.py --check; then
        print_error "❌ Version consistency check failed"
        exit 1
    fi
else
    print_info "   [DRY RUN] Would verify version consistency"
fi

if [[ "$DO_COMMIT" == "true" ]]; then
    print_status "📝 Committing version bump..."

    if [[ "$DRY_RUN" == "false" ]]; then
        git add "${RELEASE_FILES[@]}"
        git commit -m "🔖 Bump version to $NEW_VERSION

- Updated version in all configuration files
- All tests passing
- Ready for release"
    else
        print_info "   [DRY RUN] Would stage: ${RELEASE_FILES[*]}"
        print_info "   [DRY RUN] Would commit with message: 'Bump version to $NEW_VERSION'"
    fi
else
    print_warning "⚠️  Skipping commit (--no-commit flag used)"
fi

if [[ "$DO_TAG" == "true" ]]; then
    print_status "🏷️  Creating git tag v$NEW_VERSION..."

    if [[ "$DRY_RUN" == "false" ]]; then
        git tag "v$NEW_VERSION" -m "Catzilla v$NEW_VERSION

Release v$NEW_VERSION

## What's New
- Version bump to $NEW_VERSION
- All tests passing
- Ready for distribution"
    else
        print_info "   [DRY RUN] Would create tag: v$NEW_VERSION"
    fi
else
    print_warning "⚠️  Skipping tag creation (--no-tag flag used)"
fi

print_header "✅ Version bump completed successfully!"
echo ""
print_info "📋 Summary:"
print_info "   Version: $NEW_VERSION"
print_info "   Tests run: $RUN_TESTS"
print_info "   Committed: $DO_COMMIT"
print_info "   Tagged: $DO_TAG"
echo ""

if [[ "$DRY_RUN" == "false" ]]; then
    print_status "📋 Next steps:"
    if [[ -n "$CURRENT_BRANCH" ]]; then
        print_status "   git push origin $CURRENT_BRANCH"
    else
        print_status "   git push origin <branch>"
    fi
    print_status "   git push origin v$NEW_VERSION"
    echo ""
    print_status "🚀 This will trigger the release workflow and create:"
    print_status "   - GitHub Release with pre-built wheels"
    print_status "   - Updated documentation"
    print_status "   - Performance benchmarks"
    echo ""

    read -p "Do you want to push to GitHub now? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "🚀 Pushing to GitHub..."
        if [[ -n "$CURRENT_BRANCH" ]]; then
            git push origin "$CURRENT_BRANCH"
        else
            print_error "❌ Could not determine current branch automatically"
            exit 1
        fi
        git push origin "v$NEW_VERSION"
        print_status "✅ Successfully pushed to GitHub!"
        print_info "🔗 Check the release at: https://github.com/rezwanahmedsami/catzilla/releases/tag/v$NEW_VERSION"
    else
        print_info "Remember to push when ready:"
        if [[ -n "$CURRENT_BRANCH" ]]; then
            print_info "   git push origin $CURRENT_BRANCH && git push origin v$NEW_VERSION"
        else
            print_info "   git push origin <branch> && git push origin v$NEW_VERSION"
        fi
    fi
else
    print_warning "DRY RUN completed - no actual changes made"
fi
