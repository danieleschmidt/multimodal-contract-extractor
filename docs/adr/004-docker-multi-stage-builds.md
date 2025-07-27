# ADR 004: Use Docker Multi-Stage Builds for Production Images

## Status
Accepted

## Context
The multimodal contract extractor needs to be containerized for consistent deployment across different environments. The application has several build dependencies (build tools, development packages) that are not needed in the production runtime, and we need to optimize for:

- **Image Size**: Minimize production image size for faster deployments and reduced storage costs
- **Security**: Reduce attack surface by excluding unnecessary packages and files
- **Performance**: Faster container startup and reduced resource usage
- **Build Efficiency**: Efficient build process with proper layer caching

## Decision
We will use Docker multi-stage builds to create optimized production images.

## Rationale

### Multi-Stage Build Benefits:
- **Smaller Production Images**: Build dependencies are left in intermediate stages
- **Better Security**: Only necessary runtime components in final image
- **Clear Separation**: Development tools separated from production runtime
- **Build Optimization**: Better layer caching and parallel build stages
- **Flexibility**: Different target stages for different environments (dev, test, prod)

### Current Implementation:
```dockerfile
# Build stage
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y build-essential pkg-config
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage  
FROM python:3.11-slim as production
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils
COPY --from=builder /root/.local /home/appuser/.local
# ... rest of production setup
```

### Considered Alternatives:
- **Single-Stage Build**: Simpler but results in larger images with unnecessary build tools
- **Alpine Linux Base**: Smaller base image but compatibility issues with some Python packages
- **Distroless Images**: Minimal images but complex setup for Python applications
- **BuildKit Advanced Features**: More complex but offers additional optimization opportunities

## Implementation Details

### Build Stages:

#### 1. Builder Stage (`builder`)
- **Base Image**: `python:3.11-slim`
- **Purpose**: Install build dependencies and compile Python packages
- **Contents**: Build tools, development headers, source code compilation
- **Optimizations**: Parallel pip installs, build cache utilization

#### 2. Production Stage (`production`)
- **Base Image**: `python:3.11-slim`
- **Purpose**: Minimal runtime environment for production deployment
- **Contents**: Only runtime dependencies, application code, and system libraries
- **Security**: Non-root user, minimal package set, health checks

### Development vs Production Targets:
```dockerfile
# Development target (includes debugging tools)
FROM builder as development
RUN pip install --user debugpy pytest-cov
COPY . .
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "web_app.py"]

# Production target (optimized for size and security)
FROM production as runtime
USER appuser
CMD ["python", "web_app.py"]
```

### Build Optimization Strategies:
1. **Layer Caching**: Order Dockerfile commands from least to most frequently changing
2. **Dependency Installation**: Install dependencies before copying source code
3. **Parallel Builds**: Use BuildKit for parallel stage execution
4. **Build Args**: Parameterize builds for different environments
5. **Cache Mounts**: Use build cache mounts for package managers

### Security Enhancements:
- **Non-root User**: Application runs as dedicated non-root user
- **Minimal Packages**: Only essential runtime packages installed
- **Security Updates**: Regular base image updates with security patches
- **File Permissions**: Proper file ownership and permissions
- **Health Checks**: Built-in health check endpoints

## Build Process

### Local Development:
```bash
# Build development image with debugging tools
docker build --target development -t mce:dev .

# Build production image
docker build --target production -t mce:prod .

# Multi-platform builds
docker buildx build --platform linux/amd64,linux/arm64 --target production -t mce:prod .
```

### CI/CD Pipeline:
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v4
  with:
    context: .
    target: production
    platforms: linux/amd64,linux/arm64
    push: true
    tags: |
      ghcr.io/org/mce:latest
      ghcr.io/org/mce:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Consequences

### Positive:
- **Reduced Image Size**: 40-60% smaller production images
- **Improved Security**: Minimal attack surface with fewer packages
- **Faster Deployments**: Smaller images deploy faster
- **Better Resource Utilization**: Lower memory footprint in production
- **Development Flexibility**: Different targets for different use cases

### Negative:
- **Build Complexity**: More complex Dockerfile structure
- **Build Time**: Potentially longer initial build times
- **Debugging Challenges**: Production images harder to debug
- **Maintenance Overhead**: Multiple stages to maintain and optimize

### Risks and Mitigations:
- **Risk**: Missing runtime dependencies in production stage
  - **Mitigation**: Comprehensive testing of production images before deployment
- **Risk**: Build cache invalidation causing slow builds
  - **Mitigation**: Optimize Dockerfile layer ordering and use build cache mounts
- **Risk**: Security vulnerabilities in base images
  - **Mitigation**: Regular base image updates and vulnerability scanning

## Metrics and Monitoring

### Build Metrics:
- Build time by stage
- Final image size
- Layer cache hit rates
- Build success rates

### Runtime Metrics:
- Container startup time
- Memory usage comparison
- Security scan results
- Deployment time improvements

## Best Practices

### Dockerfile Optimization:
1. **Use .dockerignore**: Exclude unnecessary files from build context
2. **Minimize Layers**: Combine related RUN commands
3. **Leverage BuildKit**: Use advanced BuildKit features for optimization
4. **Pin Base Images**: Use specific image tags for reproducible builds
5. **Regular Updates**: Keep base images updated with security patches

### Security Guidelines:
1. **Scan Images**: Regular vulnerability scanning with tools like Trivy
2. **Minimal Packages**: Only install necessary runtime packages
3. **User Permissions**: Run as non-root user with minimal privileges
4. **Secrets Management**: Never include secrets in images
5. **Regular Audits**: Periodic security audits of image contents

## Future Considerations

### Potential Improvements:
- **Distroless Base Images**: Evaluate Google distroless images for even smaller footprint
- **Multi-Architecture Builds**: Native support for ARM64 architectures
- **Advanced Caching**: Implement more sophisticated caching strategies
- **Build Optimization**: Continuous optimization based on metrics and feedback

### Technology Evolution:
- **BuildKit Features**: Adopt new BuildKit capabilities as they become available
- **Container Standards**: Stay current with OCI and container industry standards
- **Security Tools**: Integrate emerging security scanning and hardening tools

## References
- [Docker Multi-Stage Builds Documentation](https://docs.docker.com/develop/dev-best-practices/dockerfile_best-practices/#use-multi-stage-builds)
- [BuildKit Documentation](https://docs.docker.com/buildx/working-with-buildx/)
- [Container Security Best Practices](https://snyk.io/blog/10-docker-image-security-best-practices/)
- [Python Docker Best Practices](https://pythonspeed.com/articles/docker-python-production/)

## Revision History
- 2024-01-16: Initial version
- 2024-01-18: Added security enhancements and build optimization details
- 2024-01-20: Updated with CI/CD integration examples