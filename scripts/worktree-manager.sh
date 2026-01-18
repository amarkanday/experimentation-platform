#!/bin/bash
# Git Worktree Manager for Multi-Claude Workflows
# Manages multiple git worktrees for parallel development

set -e

WORKTREE_BASE="../experimentation-platform-worktrees"
SCRIPT_NAME=$(basename "$0")

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Function to create a worktree
create_worktree() {
  local task_name=$1

  if [ -z "$task_name" ]; then
    print_error "Task name required"
    echo "Usage: $SCRIPT_NAME create <task-name>"
    exit 1
  fi

  local branch_name="feature/$task_name"
  local worktree_path="$WORKTREE_BASE/$task_name"

  print_info "Creating worktree for: $task_name"

  # Create base directory if it doesn't exist
  mkdir -p "$WORKTREE_BASE"

  # Check if worktree already exists
  if [ -d "$worktree_path" ]; then
    print_error "Worktree already exists at: $worktree_path"
    exit 1
  fi

  # Check if branch already exists
  if git show-ref --verify --quiet "refs/heads/$branch_name"; then
    print_warning "Branch $branch_name already exists, using existing branch"
    git worktree add "$worktree_path" "$branch_name"
  else
    print_info "Creating new branch: $branch_name"
    git worktree add -b "$branch_name" "$worktree_path"
  fi

  print_success "Worktree created successfully!"
  echo ""
  echo "📂 Location: $worktree_path"
  echo "🌿 Branch:   $branch_name"
  echo ""
  echo "To start working:"
  echo "  cd $worktree_path"
  echo "  claude"
  echo ""
  echo "Or open in new terminal tab:"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  osascript -e 'tell application \"Terminal\" to do script \"cd $worktree_path && claude\"'"
  fi
}

# Function to list worktrees
list_worktrees() {
  print_info "Active worktrees:"
  echo ""
  git worktree list | while read -r line; do
    echo "  $line"
  done
  echo ""

  # Count worktrees
  local count=$(git worktree list | wc -l | tr -d ' ')
  local extra=$((count - 1))

  if [ $extra -eq 0 ]; then
    print_info "No additional worktrees (only main checkout)"
  else
    print_success "$extra additional worktree(s) active"
  fi
}

# Function to cleanup worktree
cleanup_worktree() {
  local task_name=$1

  if [ -z "$task_name" ]; then
    print_error "Task name required"
    echo "Usage: $SCRIPT_NAME cleanup <task-name>"
    exit 1
  fi

  local worktree_path="$WORKTREE_BASE/$task_name"
  local branch_name="feature/$task_name"

  if [ ! -d "$worktree_path" ]; then
    print_error "Worktree not found: $worktree_path"
    exit 1
  fi

  print_info "Removing worktree: $task_name"
  git worktree remove "$worktree_path"
  print_success "Worktree removed"

  # Ask about branch deletion
  echo ""
  read -p "Delete branch $branch_name? (y/N) " -n 1 -r
  echo ""

  if [[ $REPLY =~ ^[Yy]$ ]]; then
    git branch -D "$branch_name"
    print_success "Branch deleted"
  else
    print_info "Branch $branch_name kept"
  fi
}

# Function to open worktree in new terminal
open_worktree() {
  local task_name=$1

  if [ -z "$task_name" ]; then
    print_error "Task name required"
    echo "Usage: $SCRIPT_NAME open <task-name>"
    exit 1
  fi

  local worktree_path="$WORKTREE_BASE/$task_name"

  if [ ! -d "$worktree_path" ]; then
    print_error "Worktree not found: $worktree_path"
    exit 1
  fi

  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - open in new Terminal tab
    osascript -e "tell application \"Terminal\" to do script \"cd $worktree_path && echo 'Worktree: $task_name' && echo 'Ready to start Claude' && exec bash\""
    print_success "Opened worktree in new Terminal tab"
  else
    print_info "Opening worktree at: $worktree_path"
    echo "Run: cd $worktree_path && claude"
  fi
}

# Function to show status of all worktrees
status_worktrees() {
  print_info "Worktree Status:"
  echo ""

  git worktree list --porcelain | awk '
    /^worktree/ { worktree=$2 }
    /^branch/ {
      branch=$2
      gsub(/.*\//, "", branch)
    }
    /^$/ {
      if (worktree != "") {
        printf "  📂 %-30s 🌿 %s\n", worktree, branch
        worktree=""
        branch=""
      }
    }
  '
  echo ""
}

# Function to sync all worktrees
sync_worktrees() {
  print_info "Syncing all worktrees with main..."

  # Get current worktree
  CURRENT_DIR=$(pwd)

  # For each worktree
  git worktree list --porcelain | grep "^worktree" | cut -d' ' -f2 | while read -r worktree_path; do
    if [ "$worktree_path" != "$CURRENT_DIR" ]; then
      print_info "Syncing: $worktree_path"
      (
        cd "$worktree_path"
        git fetch origin
        print_success "Synced: $worktree_path"
      )
    fi
  done

  print_success "All worktrees synced"
}

# Show usage
show_usage() {
  cat << EOF
Git Worktree Manager for Multi-Claude Workflows

Usage:
  $SCRIPT_NAME <command> [arguments]

Commands:
  create <task-name>    Create a new worktree for a task
  list                  List all active worktrees
  status                Show detailed status of all worktrees
  open <task-name>      Open worktree in new terminal tab
  cleanup <task-name>   Remove a worktree (prompts for branch deletion)
  sync                  Sync all worktrees with remote
  help                  Show this help message

Examples:
  $SCRIPT_NAME create metrics-dashboard
  $SCRIPT_NAME list
  $SCRIPT_NAME open metrics-dashboard
  $SCRIPT_NAME cleanup metrics-dashboard

Workflow:
  1. Create worktree:  $SCRIPT_NAME create my-feature
  2. Open in terminal: cd $WORKTREE_BASE/my-feature && claude
  3. Work on feature independently
  4. When done:        $SCRIPT_NAME cleanup my-feature

Tips:
  - Each worktree is completely independent
  - You can run Claude in multiple worktrees simultaneously
  - Great for parallel feature development
  - Use descriptive task names for easy identification
EOF
}

# Main command handler
case "$1" in
  create)
    create_worktree "$2"
    ;;
  list)
    list_worktrees
    ;;
  status)
    status_worktrees
    ;;
  cleanup)
    cleanup_worktree "$2"
    ;;
  open)
    open_worktree "$2"
    ;;
  sync)
    sync_worktrees
    ;;
  help|--help|-h)
    show_usage
    ;;
  *)
    if [ -z "$1" ]; then
      show_usage
    else
      print_error "Unknown command: $1"
      echo ""
      show_usage
    fi
    exit 1
    ;;
esac
