# Advanced GitHub Actions Workflows

This document provides advanced GitHub Actions workflow configurations for production-grade SDLC automation, including performance monitoring, security scanning, and compliance automation.

**Note**: These workflows require manual setup by repository administrators as they cannot be automatically created by GitHub Apps without workflow permissions.

## Performance Monitoring Workflow

Create `.github/workflows/performance-monitoring.yml`:

```yaml
# Performance Monitoring and Benchmarking
# This workflow runs performance tests and tracks metrics over time

name: Performance Monitoring

on:
  push:
    branches: ["main"]
  pull_request:
  schedule:
    # Run performance tests daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  performance-benchmarks:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install -e .
      
      - name: Run performance benchmarks
        run: |
          python -m pytest tests/test_performance_benchmarks.py -v \
            --benchmark-json=benchmark-results.json \
            --benchmark-storage=benchmark-history
      
      - name: Store benchmark results
        uses: benchmark-action/github-action-benchmark@v1
        if: github.ref == 'refs/heads/main'
        with:
          tool: 'pytest'
          output-file-path: benchmark-results.json
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true
          comment-on-alert: true
          alert-threshold: '150%'
          fail-on-alert: true
      
      - name: Upload performance artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: performance-results
          path: |
            benchmark-results.json
            benchmark-history/
```

## Advanced Security Scanning Workflow

Create `.github/workflows/security-scanning.yml`:

```yaml
# Advanced Security Scanning Pipeline
# Comprehensive security analysis including SAST, dependency scanning, and container security

name: Security Scanning

on:
  push:
    branches: ["main"]
  pull_request:
  schedule:
    # Weekly security scan on Sundays at 3 AM UTC
    - cron: '0 3 * * 0'

jobs:
  security-analysis:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
      actions: read
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install -e .
      
      - name: Run Bandit security scan
        run: |
          bandit -r src -f json -o bandit-report.json || true
          bandit -r src -f txt -o bandit-report.txt || true
      
      - name: Run Safety dependency scan
        run: |
          safety check --json --output safety-report.json || true
          safety check --output safety-report.txt || true
      
      - name: Run pip-audit
        run: |
          pip-audit --format=json --output=pip-audit-report.json || true
          pip-audit --format=cyclonedx-json --output=sbom.json || true
      
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: python
          queries: security-extended,security-and-quality
      
      - name: Autobuild
        uses: github/codeql-action/autobuild@v2
      
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2
        with:
          category: "/language:python"
      
      - name: Upload security artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: security-reports
          path: |
            bandit-report.*
            safety-report.*
            pip-audit-report.json
            sbom.json
```

## Compliance Automation Workflow

Create `.github/workflows/compliance-automation.yml`:

```yaml
# Compliance Automation and Governance
# Automated compliance checks and policy enforcement

name: Compliance Automation

on:
  push:
    branches: ["main"]
  pull_request:
  schedule:
    # Daily compliance check at 1 AM UTC
    - cron: '0 1 * * *'

jobs:
  compliance-checks:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install -e .
      
      - name: Run compliance metrics
        run: |
          python scripts/compliance_metrics.py > compliance-report.json
      
      - name: License compliance check
        run: |
          pip install pip-licenses
          pip-licenses --format=json --output-file=licenses.json
          python scripts/check_license_compliance.py
      
      - name: Data privacy compliance scan
        run: |
          python scripts/privacy_compliance_check.py
      
      - name: Generate risk assessment
        run: |
          python scripts/risk_assessment.py > risk-assessment.json
      
      - name: Upload compliance artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: compliance-reports
          path: |
            compliance-report.json
            licenses.json
            risk-assessment.json
      
      - name: Comment PR with compliance status
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const complianceReport = JSON.parse(fs.readFileSync('compliance-report.json'));
            const riskReport = JSON.parse(fs.readFileSync('risk-assessment.json'));
            
            const comment = `## 🛡️ Compliance & Risk Assessment
            
            **Overall Compliance Score**: ${complianceReport.overall_compliance_score}%
            **Risk Level**: ${riskReport.overall_risk_level}
            
            ### Compliance Checks
            - ✅ Security Vulnerabilities: ${complianceReport.metrics.find(m => m.name === 'security_vulnerabilities').status}
            - ✅ Code Quality: ${complianceReport.metrics.find(m => m.name === 'code_quality_score').status}
            - ✅ License Compliance: ${complianceReport.metrics.find(m => m.name === 'license_compliance').status}
            - ✅ Data Privacy: ${complianceReport.metrics.find(m => m.name === 'data_privacy_compliance').status}
            
            ### Risk Assessment
            - **Security Risk**: ${riskReport.security_risk.level}
            - **Compliance Risk**: ${riskReport.compliance_risk.level}
            
            ### Recommendations
            ${riskReport.recommendations.map(r => `- ${r}`).join('\n')}
            `;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

## MLOps Training Pipeline Workflow

Create `.github/workflows/mlops-training.yml`:

```yaml
# MLOps Model Training Pipeline
# Automated model training, evaluation, and deployment

name: MLOps Training Pipeline

on:
  workflow_dispatch:
    inputs:
      data_version:
        description: 'Data version to use for training'
        required: true
        type: string
      model_type:
        description: 'Model type to train'
        required: true
        type: choice
        options:
          - ocr
          - vlm
          - classifier
      experiment_name:
        description: 'Experiment name'
        required: true
        type: string

jobs:
  training:
    runs-on: ubuntu-latest
    timeout-minutes: 480  # 8 hours
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: 'pip'
      
      - name: Install ML dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-gpu.txt
          pip install mlflow wandb
      
      - name: Download training data
        run: |
          python mlops/download_data.py --version ${{ inputs.data_version }}
      
      - name: Start MLflow tracking
        run: |
          export MLFLOW_TRACKING_URI=https://mlflow.your-domain.com
          export MLFLOW_EXPERIMENT_NAME=${{ inputs.experiment_name }}
      
      - name: Train model
        run: |
          python mlops/train_model.py \
            --model-type ${{ inputs.model_type }} \
            --data-version ${{ inputs.data_version }} \
            --experiment-name ${{ inputs.experiment_name }} \
            --gpu-enabled false
      
      - name: Evaluate model
        run: |
          python mlops/evaluate_model.py \
            --model-path models/latest \
            --test-data-path data/test \
            --output-path evaluation-results.json
      
      - name: Upload model artifacts
        uses: actions/upload-artifact@v3
        with:
          name: model-artifacts-${{ inputs.model_type }}
          path: |
            models/
            evaluation-results.json
            training-logs/
      
      - name: Register model
        if: success()
        run: |
          python mlops/register_model.py \
            --model-path models/latest \
            --model-type ${{ inputs.model_type }} \
            --performance-metrics evaluation-results.json
```

## Blue-Green Deployment Workflow

Create `.github/workflows/blue-green-deploy.yml`:

```yaml
# Blue-Green Model Deployment
# Safe production deployment with automated rollback

name: Blue-Green Model Deployment

on:
  workflow_dispatch:
    inputs:
      model_version:
        description: 'Model version to deploy'
        required: true
        type: string
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        run: |
          aws eks update-kubeconfig --region us-west-2 --name contract-extractor-cluster
      
      - name: Download model artifacts
        run: |
          python mlops/download_model.py --version ${{ inputs.model_version }}
      
      - name: Deploy to blue environment
        run: |
          kubectl apply -f mlops/k8s/blue-deployment.yaml
          kubectl set image deployment/contract-extractor-blue \
            app=contract-extractor:${{ inputs.model_version }}
      
      - name: Run health checks
        run: |
          python mlops/health_check.py --environment blue --timeout 300
      
      - name: Run smoke tests
        run: |
          python mlops/smoke_tests.py --environment blue
      
      - name: Switch traffic to blue
        if: success()
        run: |
          kubectl patch service contract-extractor-service \
            -p '{"spec":{"selector":{"version":"blue"}}}'
      
      - name: Monitor metrics
        run: |
          python mlops/monitor_deployment.py --duration 600  # 10 minutes
      
      - name: Rollback on failure
        if: failure()
        run: |
          kubectl patch service contract-extractor-service \
            -p '{"spec":{"selector":{"version":"green"}}}'
          echo "Deployment failed - rolled back to green environment"
```

## Setup Instructions

1. **Create Workflow Files**: Copy the above workflow contents into the corresponding files in `.github/workflows/`

2. **Configure Secrets**: Add the following secrets to your repository:
   - `MLFLOW_TRACKING_URI`: MLflow server URL
   - `AWS_ACCESS_KEY_ID`: AWS access key for EKS
   - `AWS_SECRET_ACCESS_KEY`: AWS secret key
   - `KUBECONFIG_DATA`: Base64 encoded kubeconfig

3. **Install Dependencies**: Ensure all required Python packages are in requirements files

4. **Configure Permissions**: Grant necessary permissions for security scanning and deployment

5. **Test Workflows**: Run workflows manually first to verify configuration

## Integration Points

- **Monitoring**: Workflows integrate with Prometheus metrics and Grafana dashboards
- **Security**: Results feed into security dashboards and alerting systems  
- **Compliance**: Automated compliance reports for audit and governance
- **MLOps**: Complete model lifecycle with training, evaluation, and deployment

These advanced workflows provide enterprise-grade automation for mature repositories with comprehensive monitoring, security, and compliance capabilities.