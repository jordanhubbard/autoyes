# AutoYes Examples

Real-world examples of using AutoYes with various tools.

## AI & Development Tools

### Claude
```bash
# Run Claude with auto-approval
autoyes claude

# With specific model
autoyes claude --model claude-3-5-sonnet-20241022

# Claude will auto-approve bash commands, file operations, etc.
```

### Cursor
```bash
# Run Cursor CLI with auto-approval
autoyes cursor

# Auto-approves code modifications, file operations
```

### Aider
```bash
# Run Aider with auto-approval
autoyes aider

# Auto-approves code changes, git commits
```

## Infrastructure as Code

### Terraform
```bash
# Apply changes with auto-approval
autoyes terraform apply

# Destroy infrastructure with auto-approval
autoyes terraform destroy

# Plan (read-only, no approvals needed)
terraform plan  # No need for autoyes

# Apply specific plan
autoyes terraform apply tfplan
```

### Pulumi
```bash
# Update stack with auto-approval
autoyes pulumi up

# Destroy stack with auto-approval
autoyes pulumi destroy

# Preview changes (no approval needed)
pulumi preview
```

### AWS CDK
```bash
# Deploy with auto-approval
autoyes cdk deploy

# Destroy with auto-approval
autoyes cdk destroy
```

## Kubernetes

### kubectl
```bash
# Apply configuration with auto-approval
autoyes kubectl apply -f deployment.yaml

# Delete resources with auto-approval
autoyes kubectl delete pod my-pod --force

# Drain node with auto-approval
autoyes kubectl drain node-1 --ignore-daemonsets
```

### Helm
```bash
# Install chart with auto-approval
autoyes helm install myapp ./mychart

# Upgrade with auto-approval
autoyes helm upgrade myapp ./mychart

# Uninstall with auto-approval
autoyes helm uninstall myapp
```

## Package Managers

### APT (Debian/Ubuntu)
```bash
# Upgrade all packages with auto-approval
autoyes apt upgrade

# Install package with auto-approval
autoyes apt install nginx

# Dist-upgrade with auto-approval
autoyes apt dist-upgrade
```

### Homebrew (macOS)
```bash
# Upgrade all formulae with auto-approval
autoyes brew upgrade

# Install package with auto-approval
autoyes brew install wget

# Cleanup with auto-approval
autoyes brew cleanup
```

### NPM
```bash
# Install dependencies with auto-approval
autoyes npm install

# Update packages with auto-approval
autoyes npm update

# Audit fix with auto-approval
autoyes npm audit fix
```

### Pip
```bash
# Install package with auto-approval
autoyes pip install requests

# Upgrade all packages with auto-approval
autoyes pip install --upgrade pip
```

## Docker

### Docker Cleanup
```bash
# Prune system with auto-approval
autoyes docker system prune

# Remove all stopped containers with auto-approval
autoyes docker container prune

# Remove unused images with auto-approval
autoyes docker image prune -a
```

### Docker Compose
```bash
# Down with volume removal (auto-approval)
autoyes docker-compose down -v

# Remove orphaned containers (auto-approval)
autoyes docker-compose down --remove-orphans
```

## Git Operations

### Dangerous Git Commands
```bash
# Clean untracked files with auto-approval
autoyes git clean -fdx

# Reset hard with auto-approval
autoyes git reset --hard HEAD

# Force push with auto-approval (dangerous!)
autoyes git push --force
```

## System Administration

### System Cleanup
```bash
# Clean package cache (Ubuntu)
autoyes apt autoremove

# Clean journald logs
autoyes journalctl --vacuum-time=7d

# Clear tmp directories
autoyes rm -rf /tmp/*
```

### Database Operations
```bash
# Drop database with auto-approval
autoyes psql -c "DROP DATABASE mydb;"

# Import large dump with confirmations
autoyes mysql < large_dump.sql
```

## CI/CD & Automation

### In Scripts
```bash
#!/bin/bash
# Deploy script with auto-approval

set -e

echo "Deploying application..."

# Build
docker build -t myapp:latest .

# Apply Terraform
autoyes terraform apply

# Deploy to Kubernetes
autoyes kubectl apply -f k8s/

# Update Helm release
autoyes helm upgrade myapp ./chart

echo "Deployment complete!"
```

### In Makefiles
```makefile
.PHONY: deploy destroy

deploy:
	@echo "Deploying infrastructure..."
	autoyes terraform apply
	autoyes kubectl apply -f k8s/

destroy:
	@echo "Destroying infrastructure..."
	autoyes terraform destroy
	autoyes kubectl delete -f k8s/
```

### In CI/CD Pipelines
```yaml
# GitHub Actions example
- name: Deploy infrastructure
  run: autoyes terraform apply
  env:
    AUTOYES_DEBUG: 1

- name: Apply Kubernetes manifests
  run: autoyes kubectl apply -f manifests/
```

## Selective Approval

### Disable for Dangerous Operations
```bash
# Start autoyes
autoyes terraform apply

# When you see a dangerous change, press Ctrl-Y to disable
# Review the change manually
# Press Enter to proceed or Ctrl-C to cancel

# Press Ctrl-Y again to re-enable auto-approval
```

### Use for Specific Operations Only
```bash
# Disable at start (Ctrl-Y immediately)
autoyes terraform apply

# [Press Ctrl-Y right away]
# [AutoYes] Auto-approve mode: OFF

# Review each change...
# When you see safe changes, press Ctrl-Y to auto-approve remaining
# [AutoYes] Auto-approve mode: ON
```

## Testing & Development

### Testing Approval Logic
```bash
# Test with Python script that asks for input
autoyes python3 test_approval.py

# Test with bash script
autoyes bash -c 'read -p "Continue? (yes/no): " answer && echo $answer'

# Test with custom script
autoyes ./my_script.sh
```

### Debugging
```bash
# Enable debug logging
AUTOYES_DEBUG=1 autoyes terraform apply

# In another terminal
tail -f ~/.autoyes/autoyes.log

# Or use make target
make log-tail
```

## Advanced Usage

### Chaining Commands
```bash
# Auto-approve multiple commands
autoyes sh -c 'terraform apply && kubectl apply -f k8s/'

# With error handling
autoyes bash -c 'set -e; terraform apply; kubectl apply -f k8s/'
```

### With Environment Variables
```bash
# Pass environment variables to command
AUTOYES_DEBUG=1 TF_VAR_env=prod autoyes terraform apply

# Or
env TF_VAR_env=prod autoyes terraform apply
```

### In Background Jobs
```bash
# Run in background (use with caution!)
autoyes long-running-command &

# Check if it's running
jobs

# Bring to foreground if needed
fg
```

## Common Patterns

### Infrastructure Deployment
```bash
#!/bin/bash
# Full stack deployment with auto-approval

set -e

echo "==> Building application"
docker build -t myapp:latest .

echo "==> Pushing to registry"
docker push myapp:latest

echo "==> Applying Terraform"
autoyes terraform apply

echo "==> Deploying to Kubernetes"
autoyes kubectl set image deployment/myapp myapp=myapp:latest

echo "==> Done!"
```

### Cleanup Everything
```bash
#!/bin/bash
# Cleanup script with auto-approval

set -e

echo "==> Cleaning Docker"
autoyes docker system prune -a

echo "==> Cleaning Kubernetes"
autoyes kubectl delete pods --field-selector status.phase=Succeeded

echo "==> Cleaning Homebrew"
autoyes brew cleanup

echo "==> Done!"
```

## Tips & Tricks

### Create Aliases
```bash
# Add to ~/.bashrc or ~/.zshrc
alias ayclaude='autoyes claude'
alias aytf='autoyes terraform'
alias aykubectl='autoyes kubectl'
```

### Combine with Watch
```bash
# Watch and auto-approve
watch -n 5 'autoyes kubectl rollout status deployment/myapp'
```

### Use with xargs
```bash
# Delete multiple resources with auto-approval
kubectl get pods | grep Completed | awk '{print $1}' | xargs -I {} autoyes kubectl delete pod {}
```

## Safety Checklist

Before using autoyes with destructive operations:

- [ ] Understand what the command will do
- [ ] Test in a safe environment first
- [ ] Have backups if applicable
- [ ] Consider using Ctrl-Y toggle for critical steps
- [ ] Enable debug logging if unsure: `AUTOYES_DEBUG=1`
- [ ] Start with `--dry-run` or plan/preview when available

## Getting Help

```bash
# Show help
autoyes --help

# Show version
autoyes --version

# Test installation
make test

# View debug log
make log-view
```
