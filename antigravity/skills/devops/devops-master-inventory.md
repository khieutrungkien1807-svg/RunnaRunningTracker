# Devops Consolidated Skills

## 📋 Table of Contents

- [Aws Serverless](#awsserverless)
- [Azure Functions](#azurefunctions)
- [Deployment Procedures](#deploymentprocedures)
- [Docker Expert](#dockerexpert)
- [Gcp Cloud Run](#gcpcloudrun)
- [Linux Shell Scripting](#linuxshellscripting)
- [Server Management](#servermanagement)
- [Vercel Deployment](#verceldeployment)

---

<a id="awsserverless"></a>

## Aws Serverless

---
name: aws-serverless
description: "Specialized skill for building production-ready serverless applications on AWS. Covers Lambda functions, API Gateway, DynamoDB, SQS/SNS event-driven patterns, SAM/CDK deployment, and cold start optimization."
source: vibeship-spawner-skills (Apache 2.0)
---

# AWS Serverless

## Patterns

### Lambda Handler Pattern

Proper Lambda function structure with error handling

**When to use**: ['Any Lambda function implementation', 'API handlers, event processors, scheduled tasks']

```python
```javascript
// Node.js Lambda Handler
// handler.js

// Initialize outside handler (reused across invocations)
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

// Handler function
exports.handler = async (event, context) => {
  // Optional: Don't wait for event loop to clear (Node.js)
  context.callbackWaitsForEmptyEventLoop = false;

  try {
    // Parse input based on event source
    const body = typeof event.body === 'string'
      ? JSON.parse(event.body)
      : event.body;

    // Business logic
    const result = await processRequest(body);

    // Return API Gateway compatible response
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify(result)
    };
  } catch (error) {
    console.error('Error:', JSON.stringify({
      error: error.message,
      stack: error.stack,
      requestId: context.awsRequestId
    }));

    return {
      statusCode: error.statusCode || 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message || 'Internal server error'
      })
    };
  }
};

async function processRequest(data) {
  // Your business logic here
  const result = await docClient.send(new GetCommand({
    TableName: process.env.TABLE_NAME,
    Key: { id: data.id }
  }));
  return result.Item;
}
```

```python
# Python Lambda Handler
# handler.py

import json
import os
import logging
import boto3
from botocore.exceptions import ClientError

# Initialize outside handler (reused across invocations)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        # Parse i
```

### API Gateway Integration Pattern

REST API and HTTP API integration with Lambda

**When to use**: ['Building REST APIs backed by Lambda', 'Need HTTP endpoints for functions']

```javascript
```yaml
# template.yaml (SAM)
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: nodejs20.x
    Timeout: 30
    MemorySize: 256
    Environment:
      Variables:
        TABLE_NAME: !Ref ItemsTable

Resources:
  # HTTP API (recommended for simple use cases)
  HttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      StageName: prod
      CorsConfiguration:
        AllowOrigins:
          - "*"
        AllowMethods:
          - GET
          - POST
          - DELETE
        AllowHeaders:
          - "*"

  # Lambda Functions
  GetItemFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handlers/get.handler
      Events:
        GetItem:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /items/{id}
            Method: GET
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref ItemsTable

  CreateItemFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handlers/create.handler
      Events:
        CreateItem:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /items
            Method: POST
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref ItemsTable

  # DynamoDB Table
  ItemsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST

Outputs:
  ApiUrl:
    Value: !Sub "https://${HttpApi}.execute-api.${AWS::Region}.amazonaws.com/prod"
```

```javascript
// src/handlers/get.js
const { getItem } = require('../lib/dynamodb');

exports.handler = async (event) => {
  const id = event.pathParameters?.id;

  if (!id) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Missing id parameter' })
    };
  }

  const item =
```

### Event-Driven SQS Pattern

Lambda triggered by SQS for reliable async processing

**When to use**: ['Decoupled, asynchronous processing', 'Need retry logic and DLQ', 'Processing messages in batches']

```python
```yaml
# template.yaml
Resources:
  ProcessorFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handlers/processor.handler
      Events:
        SQSEvent:
          Type: SQS
          Properties:
            Queue: !GetAtt ProcessingQueue.Arn
            BatchSize: 10
            FunctionResponseTypes:
              - ReportBatchItemFailures  # Partial batch failure handling

  ProcessingQueue:
    Type: AWS::SQS::Queue
    Properties:
      VisibilityTimeout: 180  # 6x Lambda timeout
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt DeadLetterQueue.Arn
        maxReceiveCount: 3

  DeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      MessageRetentionPeriod: 1209600  # 14 days
```

```javascript
// src/handlers/processor.js
exports.handler = async (event) => {
  const batchItemFailures = [];

  for (const record of event.Records) {
    try {
      const body = JSON.parse(record.body);
      await processMessage(body);
    } catch (error) {
      console.error(`Failed to process message ${record.messageId}:`, error);
      // Report this item as failed (will be retried)
      batchItemFailures.push({
        itemIdentifier: record.messageId
      });
    }
  }

  // Return failed items for retry
  return { batchItemFailures };
};

async function processMessage(message) {
  // Your processing logic
  console.log('Processing:', message);

  // Simulate work
  await saveToDatabase(message);
}
```

```python
# Python version
import json
import logging

logger = logging.getLogger()

def handler(event, context):
    batch_item_failures = []

    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            process_message(body)
        except Exception as e:
            logger.error(f"Failed to process {record['messageId']}: {e}")
            batch_item_failures.append({
                'itemIdentifier': record['messageId']
            })

    return {'batchItemFailures': batch_ite
```

## Anti-Patterns

### ❌ Monolithic Lambda

**Why bad**: Large deployment packages cause slow cold starts.
Hard to scale individual operations.
Updates affect entire system.

### ❌ Large Dependencies

**Why bad**: Increases deployment package size.
Slows down cold starts significantly.
Most of SDK/library may be unused.

### ❌ Synchronous Calls in VPC

**Why bad**: VPC-attached Lambdas have ENI setup overhead.
Blocking DNS lookups or connections worsen cold starts.

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | high | ## Measure your INIT phase |
| Issue | high | ## Set appropriate timeout |
| Issue | high | ## Increase memory allocation |
| Issue | medium | ## Verify VPC configuration |
| Issue | medium | ## Tell Lambda not to wait for event loop |
| Issue | medium | ## For large file uploads |
| Issue | high | ## Use different buckets/prefixes |


---

<a id="azurefunctions"></a>

## Azure Functions

---
name: azure-functions
description: "Expert patterns for Azure Functions development including isolated worker model, Durable Functions orchestration, cold start optimization, and production patterns. Covers .NET, Python, and Node.js programming models. Use when: azure function, azure functions, durable functions, azure serverless, function app."
source: vibeship-spawner-skills (Apache 2.0)
---

# Azure Functions

## Patterns

### Isolated Worker Model (.NET)

Modern .NET execution model with process isolation

### Node.js v4 Programming Model

Modern code-centric approach for TypeScript/JavaScript

### Python v2 Programming Model

Decorator-based approach for Python functions

## Anti-Patterns

### ❌ Blocking Async Calls

### ❌ New HttpClient Per Request

### ❌ In-Process Model for New Projects

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | high | ## Use async pattern with Durable Functions |
| Issue | high | ## Use IHttpClientFactory (Recommended) |
| Issue | high | ## Always use async/await |
| Issue | medium | ## Configure maximum timeout (Consumption) |
| Issue | high | ## Use isolated worker for new projects |
| Issue | medium | ## Configure Application Insights properly |
| Issue | medium | ## Check extension bundle (most common) |
| Issue | medium | ## Add warmup trigger to initialize your code |


---

<a id="deploymentprocedures"></a>

## Deployment Procedures

---
name: deployment-procedures
description: Production deployment principles and decision-making. Safe deployment workflows, rollback strategies, and verification. Teaches thinking, not scripts.
allowed-tools: Read, Glob, Grep, Bash
---

# Deployment Procedures

> Deployment principles and decision-making for safe production releases.
> **Learn to THINK, not memorize scripts.**

---

## ⚠️ How to Use This Skill

This skill teaches **deployment principles**, not bash scripts to copy.

- Every deployment is unique
- Understand the WHY behind each step
- Adapt procedures to your platform

---

## 1. Platform Selection

### Decision Tree

```
What are you deploying?
│
├── Static site / JAMstack
│   └── Vercel, Netlify, Cloudflare Pages
│
├── Simple web app
│   ├── Managed → Railway, Render, Fly.io
│   └── Control → VPS + PM2/Docker
│
├── Microservices
│   └── Container orchestration
│
└── Serverless
    └── Edge functions, Lambda
```

### Each Platform Has Different Procedures

| Platform | Deployment Method |
|----------|------------------|
| **Vercel/Netlify** | Git push, auto-deploy |
| **Railway/Render** | Git push or CLI |
| **VPS + PM2** | SSH + manual steps |
| **Docker** | Image push + orchestration |
| **Kubernetes** | kubectl apply |

---

## 2. Pre-Deployment Principles

### The 4 Verification Categories

| Category | What to Check |
|----------|--------------|
| **Code Quality** | Tests passing, linting clean, reviewed |
| **Build** | Production build works, no warnings |
| **Environment** | Env vars set, secrets current |
| **Safety** | Backup done, rollback plan ready |

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Production build successful
- [ ] Environment variables verified
- [ ] Database migrations ready (if any)
- [ ] Rollback plan documented
- [ ] Team notified
- [ ] Monitoring ready

---

## 3. Deployment Workflow Principles

### The 5-Phase Process

```
1. PREPARE
   └── Verify code, build, env vars

2. BACKUP
   └── Save current state before changing

3. DEPLOY
   └── Execute with monitoring open

4. VERIFY
   └── Health check, logs, key flows

5. CONFIRM or ROLLBACK
   └── All good? Confirm. Issues? Rollback.
```

### Phase Principles

| Phase | Principle |
|-------|-----------|
| **Prepare** | Never deploy untested code |
| **Backup** | Can't rollback without backup |
| **Deploy** | Watch it happen, don't walk away |
| **Verify** | Trust but verify |
| **Confirm** | Have rollback trigger ready |

---

## 4. Post-Deployment Verification

### What to Verify

| Check | Why |
|-------|-----|
| **Health endpoint** | Service is running |
| **Error logs** | No new errors |
| **Key user flows** | Critical features work |
| **Performance** | Response times acceptable |

### Verification Window

- **First 5 minutes**: Active monitoring
- **15 minutes**: Confirm stable
- **1 hour**: Final verification
- **Next day**: Review metrics

---

## 5. Rollback Principles

### When to Rollback

| Symptom | Action |
|---------|--------|
| Service down | Rollback immediately |
| Critical errors | Rollback |
| Performance >50% degraded | Consider rollback |
| Minor issues | Fix forward if quick |

### Rollback Strategy by Platform

| Platform | Rollback Method |
|----------|----------------|
| **Vercel/Netlify** | Redeploy previous commit |
| **Railway/Render** | Rollback in dashboard |
| **VPS + PM2** | Restore backup, restart |
| **Docker** | Previous image tag |
| **K8s** | kubectl rollout undo |

### Rollback Principles

1. **Speed over perfection**: Rollback first, debug later
2. **Don't compound errors**: One rollback, not multiple changes
3. **Communicate**: Tell team what happened
4. **Post-mortem**: Understand why after stable

---

## 6. Zero-Downtime Deployment

### Strategies

| Strategy | How It Works |
|----------|--------------|
| **Rolling** | Replace instances one by one |
| **Blue-Green** | Switch traffic between environments |
| **Canary** | Gradual traffic shift |

### Selection Principles

| Scenario | Strategy |
|----------|----------|
| Standard release | Rolling |
| High-risk change | Blue-green (easy rollback) |
| Need validation | Canary (test with real traffic) |

---

## 7. Emergency Procedures

### Service Down Priority

1. **Assess**: What's the symptom?
2. **Quick fix**: Restart if unclear
3. **Rollback**: If restart doesn't help
4. **Investigate**: After stable

### Investigation Order

| Check | Common Issues |
|-------|--------------|
| **Logs** | Errors, exceptions |
| **Resources** | Disk full, memory |
| **Network** | DNS, firewall |
| **Dependencies** | Database, APIs |

---

## 8. Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Deploy on Friday | Deploy early in week |
| Rush deployment | Follow the process |
| Skip staging | Always test first |
| Deploy without backup | Backup before deploy |
| Walk away after deploy | Monitor for 15+ min |
| Multiple changes at once | One change at a time |

---

## 9. Decision Checklist

Before deploying:

- [ ] **Platform-appropriate procedure?**
- [ ] **Backup strategy ready?**
- [ ] **Rollback plan documented?**
- [ ] **Monitoring configured?**
- [ ] **Team notified?**
- [ ] **Time to monitor after?**

---

## 10. Best Practices

1. **Small, frequent deploys** over big releases
2. **Feature flags** for risky changes
3. **Automate** repetitive steps
4. **Document** every deployment
5. **Review** what went wrong after issues
6. **Test rollback** before you need it

---

> **Remember:** Every deployment is a risk. Minimize risk through preparation, not speed.


---

<a id="dockerexpert"></a>

## Docker Expert

---
name: docker-expert
description: Docker containerization expert with deep knowledge of multi-stage builds, image optimization, container security, Docker Compose orchestration, and production deployment patterns. Use PROACTIVELY for Dockerfile optimization, container issues, image size problems, security hardening, networking, and orchestration challenges.
category: devops
color: blue
displayName: Docker Expert
---

# Docker Expert

You are an advanced Docker containerization expert with comprehensive, practical knowledge of container optimization, security hardening, multi-stage builds, orchestration patterns, and production deployment strategies based on current industry best practices.

## When invoked:

0. If the issue requires ultra-specific expertise outside Docker, recommend switching and stop:
   - Kubernetes orchestration, pods, services, ingress → kubernetes-expert (future)
   - GitHub Actions CI/CD with containers → github-actions-expert
   - AWS ECS/Fargate or cloud-specific container services → devops-expert
   - Database containerization with complex persistence → database-expert

   Example to output:
   "This requires Kubernetes orchestration expertise. Please invoke: 'Use the kubernetes-expert subagent.' Stopping here."

1. Analyze container setup comprehensively:

   **Use internal tools first (Read, Grep, Glob) for better performance. Shell commands are fallbacks.**

   ```bash
   # Docker environment detection
   docker --version 2>/dev/null || echo "No Docker installed"
   docker info | grep -E "Server Version|Storage Driver|Container Runtime" 2>/dev/null
   docker context ls 2>/dev/null | head -3

   # Project structure analysis
   find . -name "Dockerfile*" -type f | head -10
   find . -name "*compose*.yml" -o -name "*compose*.yaml" -type f | head -5
   find . -name ".dockerignore" -type f | head -3

   # Container status if running
   docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null | head -10
   docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null | head -10
   ```

   **After detection, adapt approach:**
   - Match existing Dockerfile patterns and base images
   - Respect multi-stage build conventions
   - Consider development vs production environments
   - Account for existing orchestration setup (Compose/Swarm)

2. Identify the specific problem category and complexity level

3. Apply the appropriate solution strategy from my expertise

4. Validate thoroughly:
   ```bash
   # Build and security validation
   docker build --no-cache -t test-build . 2>/dev/null && echo "Build successful"
   docker history test-build --no-trunc 2>/dev/null | head -5
   docker scout quickview test-build 2>/dev/null || echo "No Docker Scout"

   # Runtime validation
   docker run --rm -d --name validation-test test-build 2>/dev/null
   docker exec validation-test ps aux 2>/dev/null | head -3
   docker stop validation-test 2>/dev/null

   # Compose validation
   docker-compose config 2>/dev/null && echo "Compose config valid"
   ```

## Core Expertise Areas

### 1. Dockerfile Optimization & Multi-Stage Builds

**High-priority patterns I address:**
- **Layer caching optimization**: Separate dependency installation from source code copying
- **Multi-stage builds**: Minimize production image size while keeping build flexibility
- **Build context efficiency**: Comprehensive .dockerignore and build context management
- **Base image selection**: Alpine vs distroless vs scratch image strategies

**Key techniques:**
```dockerfile
# Optimized multi-stage pattern
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --production

FROM node:18-alpine AS runtime
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=build --chown=nextjs:nodejs /app/dist ./dist
COPY --from=build --chown=nextjs:nodejs /app/package*.json ./
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

### 2. Container Security Hardening

**Security focus areas:**
- **Non-root user configuration**: Proper user creation with specific UID/GID
- **Secrets management**: Docker secrets, build-time secrets, avoiding env vars
- **Base image security**: Regular updates, minimal attack surface
- **Runtime security**: Capability restrictions, resource limits

**Security patterns:**
```dockerfile
# Security-hardened container
FROM node:18-alpine
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup
WORKDIR /app
COPY --chown=appuser:appgroup package*.json ./
RUN npm ci --only=production
COPY --chown=appuser:appgroup . .
USER 1001
# Drop capabilities, set read-only root filesystem
```

### 3. Docker Compose Orchestration

**Orchestration expertise:**
- **Service dependency management**: Health checks, startup ordering
- **Network configuration**: Custom networks, service discovery
- **Environment management**: Dev/staging/prod configurations
- **Volume strategies**: Named volumes, bind mounts, data persistence

**Production-ready compose pattern:**
```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      target: production
    depends_on:
      db:
        condition: service_healthy
    networks:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB_FILE: /run/secrets/db_name
      POSTGRES_USER_FILE: /run/secrets/db_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_name
      - db_user
      - db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  postgres_data:

secrets:
  db_name:
    external: true
  db_user:
    external: true
  db_password:
    external: true
```

### 4. Image Size Optimization

**Size reduction strategies:**
- **Distroless images**: Minimal runtime environments
- **Build artifact optimization**: Remove build tools and cache
- **Layer consolidation**: Combine RUN commands strategically
- **Multi-stage artifact copying**: Only copy necessary files

**Optimization techniques:**
```dockerfile
# Minimal production image
FROM gcr.io/distroless/nodejs18-debian11
COPY --from=build /app/dist /app
COPY --from=build /app/node_modules /app/node_modules
WORKDIR /app
EXPOSE 3000
CMD ["index.js"]
```

### 5. Development Workflow Integration

**Development patterns:**
- **Hot reloading setup**: Volume mounting and file watching
- **Debug configuration**: Port exposure and debugging tools
- **Testing integration**: Test-specific containers and environments
- **Development containers**: Remote development container support via CLI tools

**Development workflow:**
```yaml
# Development override
services:
  app:
    build:
      context: .
      target: development
    volumes:
      - .:/app
      - /app/node_modules
      - /app/dist
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    ports:
      - "9229:9229"  # Debug port
    command: npm run dev
```

### 6. Performance & Resource Management

**Performance optimization:**
- **Resource limits**: CPU, memory constraints for stability
- **Build performance**: Parallel builds, cache utilization
- **Runtime performance**: Process management, signal handling
- **Monitoring integration**: Health checks, metrics exposure

**Resource management:**
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

## Advanced Problem-Solving Patterns

### Cross-Platform Builds
```bash
# Multi-architecture builds
docker buildx create --name multiarch-builder --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myapp:latest --push .
```

### Build Cache Optimization
```dockerfile
# Mount build cache for package managers
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production
```

### Secrets Management
```dockerfile
# Build-time secrets (BuildKit)
FROM alpine
RUN --mount=type=secret,id=api_key \
    API_KEY=$(cat /run/secrets/api_key) && \
    # Use API_KEY for build process
```

### Health Check Strategies
```dockerfile
# Sophisticated health monitoring
COPY health-check.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/health-check.sh
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD ["/usr/local/bin/health-check.sh"]
```

## Code Review Checklist

When reviewing Docker configurations, focus on:

### Dockerfile Optimization & Multi-Stage Builds
- [ ] Dependencies copied before source code for optimal layer caching
- [ ] Multi-stage builds separate build and runtime environments
- [ ] Production stage only includes necessary artifacts
- [ ] Build context optimized with comprehensive .dockerignore
- [ ] Base image selection appropriate (Alpine vs distroless vs scratch)
- [ ] RUN commands consolidated to minimize layers where beneficial

### Container Security Hardening
- [ ] Non-root user created with specific UID/GID (not default)
- [ ] Container runs as non-root user (USER directive)
- [ ] Secrets managed properly (not in ENV vars or layers)
- [ ] Base images kept up-to-date and scanned for vulnerabilities
- [ ] Minimal attack surface (only necessary packages installed)
- [ ] Health checks implemented for container monitoring

### Docker Compose & Orchestration
- [ ] Service dependencies properly defined with health checks
- [ ] Custom networks configured for service isolation
- [ ] Environment-specific configurations separated (dev/prod)
- [ ] Volume strategies appropriate for data persistence needs
- [ ] Resource limits defined to prevent resource exhaustion
- [ ] Restart policies configured for production resilience

### Image Size & Performance
- [ ] Final image size optimized (avoid unnecessary files/tools)
- [ ] Build cache optimization implemented
- [ ] Multi-architecture builds considered if needed
- [ ] Artifact copying selective (only required files)
- [ ] Package manager cache cleaned in same RUN layer

### Development Workflow Integration
- [ ] Development targets separate from production
- [ ] Hot reloading configured properly with volume mounts
- [ ] Debug ports exposed when needed
- [ ] Environment variables properly configured for different stages
- [ ] Testing containers isolated from production builds

### Networking & Service Discovery
- [ ] Port exposure limited to necessary services
- [ ] Service naming follows conventions for discovery
- [ ] Network security implemented (internal networks for backend)
- [ ] Load balancing considerations addressed
- [ ] Health check endpoints implemented and tested

## Common Issue Diagnostics

### Build Performance Issues
**Symptoms**: Slow builds (10+ minutes), frequent cache invalidation
**Root causes**: Poor layer ordering, large build context, no caching strategy
**Solutions**: Multi-stage builds, .dockerignore optimization, dependency caching

### Security Vulnerabilities
**Symptoms**: Security scan failures, exposed secrets, root execution
**Root causes**: Outdated base images, hardcoded secrets, default user
**Solutions**: Regular base updates, secrets management, non-root configuration

### Image Size Problems
**Symptoms**: Images over 1GB, deployment slowness
**Root causes**: Unnecessary files, build tools in production, poor base selection
**Solutions**: Distroless images, multi-stage optimization, artifact selection

### Networking Issues
**Symptoms**: Service communication failures, DNS resolution errors
**Root causes**: Missing networks, port conflicts, service naming
**Solutions**: Custom networks, health checks, proper service discovery

### Development Workflow Problems
**Symptoms**: Hot reload failures, debugging difficulties, slow iteration
**Root causes**: Volume mounting issues, port configuration, environment mismatch
**Solutions**: Development-specific targets, proper volume strategy, debug configuration

## Integration & Handoff Guidelines

**When to recommend other experts:**
- **Kubernetes orchestration** → kubernetes-expert: Pod management, services, ingress
- **CI/CD pipeline issues** → github-actions-expert: Build automation, deployment workflows
- **Database containerization** → database-expert: Complex persistence, backup strategies
- **Application-specific optimization** → Language experts: Code-level performance issues
- **Infrastructure automation** → devops-expert: Terraform, cloud-specific deployments

**Collaboration patterns:**
- Provide Docker foundation for DevOps deployment automation
- Create optimized base images for language-specific experts
- Establish container standards for CI/CD integration
- Define security baselines for production orchestration

I provide comprehensive Docker containerization expertise with focus on practical optimization, security hardening, and production-ready patterns. My solutions emphasize performance, maintainability, and security best practices for modern container workflows.

---

<a id="gcpcloudrun"></a>

## Gcp Cloud Run

---
name: gcp-cloud-run
description: "Specialized skill for building production-ready serverless applications on GCP. Covers Cloud Run services (containerized), Cloud Run Functions (event-driven), cold start optimization, and event-driven architecture with Pub/Sub."
source: vibeship-spawner-skills (Apache 2.0)
---

# GCP Cloud Run

## Patterns

### Cloud Run Service Pattern

Containerized web service on Cloud Run

**When to use**: ['Web applications and APIs', 'Need any runtime or library', 'Complex services with multiple endpoints', 'Stateless containerized workloads']

```javascript
```dockerfile
# Dockerfile - Multi-stage build for smaller image
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-slim
WORKDIR /app

# Copy only production dependencies
COPY --from=builder /app/node_modules ./node_modules
COPY src ./src
COPY package.json ./

# Cloud Run uses PORT env variable
ENV PORT=8080
EXPOSE 8080

# Run as non-root user
USER node

CMD ["node", "src/index.js"]
```

```javascript
// src/index.js
const express = require('express');
const app = express();

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// API routes
app.get('/api/items/:id', async (req, res) => {
  try {
    const item = await getItem(req.params.id);
    res.json(item);
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

const PORT = process.env.PORT || 8080;
const server = app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
```

```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/my-service:$COMMIT_SHA', '.']

  # Push the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/my-service:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'my-service'
      - '--image=gcr.io/$PROJECT_ID/my-service:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--memory=512Mi'
      - '--cpu=1'
      - '--min-instances=1'
      - '--max-instances=100'

```

### Cloud Run Functions Pattern

Event-driven functions (formerly Cloud Functions)

**When to use**: ['Simple event handlers', 'Pub/Sub message processing', 'Cloud Storage triggers', 'HTTP webhooks']

```javascript
```javascript
// HTTP Function
// index.js
const functions = require('@google-cloud/functions-framework');

functions.http('helloHttp', (req, res) => {
  const name = req.query.name || req.body.name || 'World';
  res.send(`Hello, ${name}!`);
});
```

```javascript
// Pub/Sub Function
const functions = require('@google-cloud/functions-framework');

functions.cloudEvent('processPubSub', (cloudEvent) => {
  // Decode Pub/Sub message
  const message = cloudEvent.data.message;
  const data = message.data
    ? JSON.parse(Buffer.from(message.data, 'base64').toString())
    : {};

  console.log('Received message:', data);

  // Process message
  processMessage(data);
});
```

```javascript
// Cloud Storage Function
const functions = require('@google-cloud/functions-framework');

functions.cloudEvent('processStorageEvent', async (cloudEvent) => {
  const file = cloudEvent.data;

  console.log(`Event: ${cloudEvent.type}`);
  console.log(`Bucket: ${file.bucket}`);
  console.log(`File: ${file.name}`);

  if (cloudEvent.type === 'google.cloud.storage.object.v1.finalized') {
    await processUploadedFile(file.bucket, file.name);
  }
});
```

```bash
# Deploy HTTP function
gcloud functions deploy hello-http \
  --gen2 \
  --runtime nodejs20 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1

# Deploy Pub/Sub function
gcloud functions deploy process-messages \
  --gen2 \
  --runtime nodejs20 \
  --trigger-topic my-topic \
  --region us-central1

# Deploy Cloud Storage function
gcloud functions deploy process-uploads \
  --gen2 \
  --runtime nodejs20 \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=my-bucket" \
  --region us-central1
```
```

### Cold Start Optimization Pattern

Minimize cold start latency for Cloud Run

**When to use**: ['Latency-sensitive applications', 'User-facing APIs', 'High-traffic services']

```javascript
## 1. Enable Startup CPU Boost

```bash
gcloud run deploy my-service \
  --cpu-boost \
  --region us-central1
```

## 2. Set Minimum Instances

```bash
gcloud run deploy my-service \
  --min-instances 1 \
  --region us-central1
```

## 3. Optimize Container Image

```dockerfile
# Use distroless for minimal image
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM gcr.io/distroless/nodejs20-debian12
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY src ./src
CMD ["src/index.js"]
```

## 4. Lazy Initialize Heavy Dependencies

```javascript
// Lazy load heavy libraries
let bigQueryClient = null;

function getBigQueryClient() {
  if (!bigQueryClient) {
    const { BigQuery } = require('@google-cloud/bigquery');
    bigQueryClient = new BigQuery();
  }
  return bigQueryClient;
}

// Only initialize when needed
app.get('/api/analytics', async (req, res) => {
  const client = getBigQueryClient();
  const results = await client.query({...});
  res.json(results);
});
```

## 5. Increase Memory (More CPU)

```bash
# Higher memory = more CPU during startup
gcloud run deploy my-service \
  --memory 1Gi \
  --cpu 2 \
  --region us-central1
```
```

## Anti-Patterns

### ❌ CPU-Intensive Work Without Concurrency=1

**Why bad**: CPU is shared across concurrent requests. CPU-bound work
will starve other requests, causing timeouts.

### ❌ Writing Large Files to /tmp

**Why bad**: /tmp is an in-memory filesystem. Large files consume
your memory allocation and can cause OOM errors.

### ❌ Long-Running Background Tasks

**Why bad**: Cloud Run throttles CPU to near-zero when not handling
requests. Background tasks will be extremely slow or stall.

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | high | ## Calculate memory including /tmp usage |
| Issue | high | ## Set appropriate concurrency |
| Issue | high | ## Enable CPU always allocated |
| Issue | medium | ## Configure connection pool with keep-alive |
| Issue | high | ## Enable startup CPU boost |
| Issue | medium | ## Explicitly set execution environment |
| Issue | medium | ## Set consistent timeouts |


---

<a id="linuxshellscripting"></a>

## Linux Shell Scripting

---
name: Linux Production Shell Scripts
description: This skill should be used when the user asks to "create bash scripts", "automate Linux tasks", "monitor system resources", "backup files", "manage users", or "write production shell scripts". It provides ready-to-use shell script templates for system administration.
metadata:
  author: zebbern
  version: "1.1"
---

# Linux Production Shell Scripts

## Purpose

Provide production-ready shell script templates for common Linux system administration tasks including backups, monitoring, user management, log analysis, and automation. These scripts serve as building blocks for security operations and penetration testing environments.

## Prerequisites

### Required Environment
- Linux/Unix system (bash shell)
- Appropriate permissions for tasks
- Required utilities installed (rsync, openssl, etc.)

### Required Knowledge
- Basic bash scripting
- Linux file system structure
- System administration concepts

## Outputs and Deliverables

1. **Backup Solutions** - Automated file and database backups
2. **Monitoring Scripts** - Resource usage tracking
3. **Automation Tools** - Scheduled task execution
4. **Security Scripts** - Password management, encryption

## Core Workflow

### Phase 1: File Backup Scripts

**Basic Directory Backup**
```bash
#!/bin/bash
backup_dir="/path/to/backup"
source_dir="/path/to/source"

# Create a timestamped backup of the source directory
tar -czf "$backup_dir/backup_$(date +%Y%m%d_%H%M%S).tar.gz" "$source_dir"
echo "Backup completed: backup_$(date +%Y%m%d_%H%M%S).tar.gz"
```

**Remote Server Backup**
```bash
#!/bin/bash
source_dir="/path/to/source"
remote_server="user@remoteserver:/path/to/backup"

# Backup files/directories to a remote server using rsync
rsync -avz --progress "$source_dir" "$remote_server"
echo "Files backed up to remote server."
```

**Backup Rotation Script**
```bash
#!/bin/bash
backup_dir="/path/to/backups"
max_backups=5

# Rotate backups by deleting the oldest if more than max_backups
while [ $(ls -1 "$backup_dir" | wc -l) -gt "$max_backups" ]; do
    oldest_backup=$(ls -1t "$backup_dir" | tail -n 1)
    rm -r "$backup_dir/$oldest_backup"
    echo "Removed old backup: $oldest_backup"
done
echo "Backup rotation completed."
```

**Database Backup Script**
```bash
#!/bin/bash
database_name="your_database"
db_user="username"
db_pass="password"
output_file="database_backup_$(date +%Y%m%d).sql"

# Perform database backup using mysqldump
mysqldump -u "$db_user" -p"$db_pass" "$database_name" > "$output_file"
gzip "$output_file"
echo "Database backup created: $output_file.gz"
```

### Phase 2: System Monitoring Scripts

**CPU Usage Monitor**
```bash
#!/bin/bash
threshold=90

# Monitor CPU usage and trigger alert if threshold exceeded
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)

if [ "$cpu_usage" -gt "$threshold" ]; then
    echo "ALERT: High CPU usage detected: $cpu_usage%"
    # Add notification logic (email, slack, etc.)
    # mail -s "CPU Alert" admin@example.com <<< "CPU usage: $cpu_usage%"
fi
```

**Disk Space Monitor**
```bash
#!/bin/bash
threshold=90
partition="/dev/sda1"

# Monitor disk usage and trigger alert if threshold exceeded
disk_usage=$(df -h | grep "$partition" | awk '{print $5}' | cut -d% -f1)

if [ "$disk_usage" -gt "$threshold" ]; then
    echo "ALERT: High disk usage detected: $disk_usage%"
    # Add alert/notification logic here
fi
```

**CPU Usage Logger**
```bash
#!/bin/bash
output_file="cpu_usage_log.txt"

# Log current CPU usage to a file with timestamp
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
cpu_usage=$(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d. -f1)
echo "$timestamp - CPU Usage: $cpu_usage%" >> "$output_file"
echo "CPU usage logged."
```

**System Health Check**
```bash
#!/bin/bash
output_file="system_health_check.txt"

# Perform system health check and save results to a file
{
    echo "System Health Check - $(date)"
    echo "================================"
    echo ""
    echo "Uptime:"
    uptime
    echo ""
    echo "Load Average:"
    cat /proc/loadavg
    echo ""
    echo "Memory Usage:"
    free -h
    echo ""
    echo "Disk Usage:"
    df -h
    echo ""
    echo "Top Processes:"
    ps aux --sort=-%cpu | head -10
} > "$output_file"

echo "System health check saved to $output_file"
```

### Phase 3: User Management Scripts

**User Account Creation**
```bash
#!/bin/bash
username="newuser"

# Check if user exists; if not, create new user
if id "$username" &>/dev/null; then
    echo "User $username already exists."
else
    useradd -m -s /bin/bash "$username"
    echo "User $username created."

    # Set password interactively
    passwd "$username"
fi
```

**Password Expiry Checker**
```bash
#!/bin/bash
output_file="password_expiry_report.txt"

# Check password expiry for users with bash shell
echo "Password Expiry Report - $(date)" > "$output_file"
echo "=================================" >> "$output_file"

IFS=$'\n'
for user in $(grep "/bin/bash" /etc/passwd | cut -d: -f1); do
    password_expires=$(chage -l "$user" 2>/dev/null | grep "Password expires" | awk -F: '{print $2}')
    echo "User: $user - Password Expires: $password_expires" >> "$output_file"
done
unset IFS

echo "Password expiry report saved to $output_file"
```

### Phase 4: Security Scripts

**Password Generator**
```bash
#!/bin/bash
length=${1:-16}

# Generate a random password
password=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9!@#$%^&*' | head -c"$length")
echo "Generated password: $password"
```

**File Encryption Script**
```bash
#!/bin/bash
file="$1"
action="${2:-encrypt}"

if [ -z "$file" ]; then
    echo "Usage: $0 <file> [encrypt|decrypt]"
    exit 1
fi

if [ "$action" == "encrypt" ]; then
    # Encrypt file using AES-256-CBC
    openssl enc -aes-256-cbc -salt -pbkdf2 -in "$file" -out "$file.enc"
    echo "File encrypted: $file.enc"
elif [ "$action" == "decrypt" ]; then
    # Decrypt file
    output_file="${file%.enc}"
    openssl enc -aes-256-cbc -d -pbkdf2 -in "$file" -out "$output_file"
    echo "File decrypted: $output_file"
fi
```

### Phase 5: Log Analysis Scripts

**Error Log Extractor**
```bash
#!/bin/bash
logfile="${1:-/var/log/syslog}"
output_file="error_log_$(date +%Y%m%d).txt"

# Extract lines with "ERROR" from the log file
grep -i "error\|fail\|critical" "$logfile" > "$output_file"
echo "Error log created: $output_file"
echo "Total errors found: $(wc -l < "$output_file")"
```

**Web Server Log Analyzer**
```bash
#!/bin/bash
log_file="${1:-/var/log/apache2/access.log}"

echo "Web Server Log Analysis"
echo "========================"
echo ""
echo "Top 10 IP Addresses:"
awk '{print $1}' "$log_file" | sort | uniq -c | sort -rn | head -10
echo ""
echo "Top 10 Requested URLs:"
awk '{print $7}' "$log_file" | sort | uniq -c | sort -rn | head -10
echo ""
echo "HTTP Status Code Distribution:"
awk '{print $9}' "$log_file" | sort | uniq -c | sort -rn
```

### Phase 6: Network Scripts

**Network Connectivity Checker**
```bash
#!/bin/bash
hosts=("8.8.8.8" "1.1.1.1" "google.com")

echo "Network Connectivity Check"
echo "=========================="

for host in "${hosts[@]}"; do
    if ping -c 1 -W 2 "$host" &>/dev/null; then
        echo "[UP] $host is reachable"
    else
        echo "[DOWN] $host is unreachable"
    fi
done
```

**Website Uptime Checker**
```bash
#!/bin/bash
websites=("https://google.com" "https://github.com")
log_file="uptime_log.txt"

echo "Website Uptime Check - $(date)" >> "$log_file"

for website in "${websites[@]}"; do
    if curl --output /dev/null --silent --head --fail --max-time 10 "$website"; then
        echo "[UP] $website is accessible" | tee -a "$log_file"
    else
        echo "[DOWN] $website is inaccessible" | tee -a "$log_file"
    fi
done
```

**Network Interface Info**
```bash
#!/bin/bash
interface="${1:-eth0}"

echo "Network Interface Information: $interface"
echo "========================================="
ip addr show "$interface" 2>/dev/null || ifconfig "$interface" 2>/dev/null
echo ""
echo "Routing Table:"
ip route | grep "$interface"
```

### Phase 7: Automation Scripts

**Automated Package Installation**
```bash
#!/bin/bash
packages=("vim" "htop" "curl" "wget" "git")

echo "Installing packages..."

for package in "${packages[@]}"; do
    if dpkg -l | grep -q "^ii  $package"; then
        echo "[SKIP] $package is already installed"
    else
        sudo apt-get install -y "$package"
        echo "[INSTALLED] $package"
    fi
done

echo "Package installation completed."
```

**Task Scheduler (Cron Setup)**
```bash
#!/bin/bash
scheduled_task="/path/to/your_script.sh"
schedule_time="0 2 * * *"  # Run at 2 AM daily

# Add task to crontab
(crontab -l 2>/dev/null; echo "$schedule_time $scheduled_task") | crontab -
echo "Task scheduled: $schedule_time $scheduled_task"
```

**Service Restart Script**
```bash
#!/bin/bash
service_name="${1:-apache2}"

# Restart a specified service
if systemctl is-active --quiet "$service_name"; then
    echo "Restarting $service_name..."
    sudo systemctl restart "$service_name"
    echo "Service $service_name restarted."
else
    echo "Service $service_name is not running. Starting..."
    sudo systemctl start "$service_name"
    echo "Service $service_name started."
fi
```

### Phase 8: File Operations

**Directory Synchronization**
```bash
#!/bin/bash
source_dir="/path/to/source"
destination_dir="/path/to/destination"

# Synchronize directories using rsync
rsync -avz --delete "$source_dir/" "$destination_dir/"
echo "Directories synchronized successfully."
```

**Data Cleanup Script**
```bash
#!/bin/bash
directory="${1:-/tmp}"
days="${2:-7}"

echo "Cleaning files older than $days days in $directory"

# Remove files older than specified days
find "$directory" -type f -mtime +"$days" -exec rm -v {} \;
echo "Cleanup completed."
```

**Folder Size Checker**
```bash
#!/bin/bash
folder_path="${1:-.}"

echo "Folder Size Analysis: $folder_path"
echo "===================================="

# Display sizes of subdirectories sorted by size
du -sh "$folder_path"/* 2>/dev/null | sort -rh | head -20
echo ""
echo "Total size:"
du -sh "$folder_path"
```

### Phase 9: System Information

**System Info Collector**
```bash
#!/bin/bash
output_file="system_info_$(hostname)_$(date +%Y%m%d).txt"

{
    echo "System Information Report"
    echo "Generated: $(date)"
    echo "========================="
    echo ""
    echo "Hostname: $(hostname)"
    echo "OS: $(uname -a)"
    echo ""
    echo "CPU Info:"
    lscpu | grep -E "Model name|CPU\(s\)|Thread"
    echo ""
    echo "Memory:"
    free -h
    echo ""
    echo "Disk Space:"
    df -h
    echo ""
    echo "Network Interfaces:"
    ip -br addr
    echo ""
    echo "Logged In Users:"
    who
} > "$output_file"

echo "System info saved to $output_file"
```

### Phase 10: Git and Development

**Git Repository Updater**
```bash
#!/bin/bash
git_repos=("/path/to/repo1" "/path/to/repo2")

for repo in "${git_repos[@]}"; do
    if [ -d "$repo/.git" ]; then
        echo "Updating repository: $repo"
        cd "$repo"
        git fetch --all
        git pull origin "$(git branch --show-current)"
        echo "Updated: $repo"
    else
        echo "Not a git repository: $repo"
    fi
done

echo "All repositories updated."
```

**Remote Script Execution**
```bash
#!/bin/bash
remote_server="${1:-user@remote-server}"
remote_script="${2:-/path/to/remote/script.sh}"

# Execute a script on a remote server via SSH
ssh "$remote_server" "bash -s" < "$remote_script"
echo "Remote script executed on $remote_server"
```

## Quick Reference

### Common Script Patterns

| Pattern | Purpose |
|---------|---------|
| `#!/bin/bash` | Shebang for bash |
| `$(date +%Y%m%d)` | Date formatting |
| `$((expression))` | Arithmetic |
| `${var:-default}` | Default value |
| `"$@"` | All arguments |

### Useful Commands

| Command | Purpose |
|---------|---------|
| `chmod +x script.sh` | Make executable |
| `./script.sh` | Run script |
| `nohup ./script.sh &` | Run in background |
| `crontab -e` | Edit cron jobs |
| `source script.sh` | Run in current shell |

### Cron Format
Minute(0-59) Hour(0-23) Day(1-31) Month(1-12) Weekday(0-7, 0/7=Sun)

## Constraints and Limitations

- Always test scripts in non-production first
- Use absolute paths to avoid errors
- Quote variables to handle spaces properly
- Many scripts require root/sudo privileges
- Use `bash -x script.sh` for debugging


---

<a id="servermanagement"></a>

## Server Management

---
name: server-management
description: Server management principles and decision-making. Process management, monitoring strategy, and scaling decisions. Teaches thinking, not commands.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Server Management

> Server management principles for production operations.
> **Learn to THINK, not memorize commands.**

---

## 1. Process Management Principles

### Tool Selection

| Scenario | Tool |
|----------|------|
| **Node.js app** | PM2 (clustering, reload) |
| **Any app** | systemd (Linux native) |
| **Containers** | Docker/Podman |
| **Orchestration** | Kubernetes, Docker Swarm |

### Process Management Goals

| Goal | What It Means |
|------|---------------|
| **Restart on crash** | Auto-recovery |
| **Zero-downtime reload** | No service interruption |
| **Clustering** | Use all CPU cores |
| **Persistence** | Survive server reboot |

---

## 2. Monitoring Principles

### What to Monitor

| Category | Key Metrics |
|----------|-------------|
| **Availability** | Uptime, health checks |
| **Performance** | Response time, throughput |
| **Errors** | Error rate, types |
| **Resources** | CPU, memory, disk |

### Alert Severity Strategy

| Level | Response |
|-------|----------|
| **Critical** | Immediate action |
| **Warning** | Investigate soon |
| **Info** | Review daily |

### Monitoring Tool Selection

| Need | Options |
|------|---------|
| Simple/Free | PM2 metrics, htop |
| Full observability | Grafana, Datadog |
| Error tracking | Sentry |
| Uptime | UptimeRobot, Pingdom |

---

## 3. Log Management Principles

### Log Strategy

| Log Type | Purpose |
|----------|---------|
| **Application logs** | Debug, audit |
| **Access logs** | Traffic analysis |
| **Error logs** | Issue detection |

### Log Principles

1. **Rotate logs** to prevent disk fill
2. **Structured logging** (JSON) for parsing
3. **Appropriate levels** (error/warn/info/debug)
4. **No sensitive data** in logs

---

## 4. Scaling Decisions

### When to Scale

| Symptom | Solution |
|---------|----------|
| High CPU | Add instances (horizontal) |
| High memory | Increase RAM or fix leak |
| Slow response | Profile first, then scale |
| Traffic spikes | Auto-scaling |

### Scaling Strategy

| Type | When to Use |
|------|-------------|
| **Vertical** | Quick fix, single instance |
| **Horizontal** | Sustainable, distributed |
| **Auto** | Variable traffic |

---

## 5. Health Check Principles

### What Constitutes Healthy

| Check | Meaning |
|-------|---------|
| **HTTP 200** | Service responding |
| **Database connected** | Data accessible |
| **Dependencies OK** | External services reachable |
| **Resources OK** | CPU/memory not exhausted |

### Health Check Implementation

- Simple: Just return 200
- Deep: Check all dependencies
- Choose based on load balancer needs

---

## 6. Security Principles

| Area | Principle |
|------|-----------|
| **Access** | SSH keys only, no passwords |
| **Firewall** | Only needed ports open |
| **Updates** | Regular security patches |
| **Secrets** | Environment vars, not files |
| **Audit** | Log access and changes |

---

## 7. Troubleshooting Priority

When something's wrong:

1. **Check if running** (process status)
2. **Check logs** (error messages)
3. **Check resources** (disk, memory, CPU)
4. **Check network** (ports, DNS)
5. **Check dependencies** (database, APIs)

---

## 8. Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Run as root | Use non-root user |
| Ignore logs | Set up log rotation |
| Skip monitoring | Monitor from day one |
| Manual restarts | Auto-restart config |
| No backups | Regular backup schedule |

---

> **Remember:** A well-managed server is boring. That's the goal.


---

<a id="verceldeployment"></a>

## Vercel Deployment

---
name: vercel-deployment
description: "Expert knowledge for deploying to Vercel with Next.js Use when: vercel, deploy, deployment, hosting, production."
source: vibeship-spawner-skills (Apache 2.0)
---

# Vercel Deployment

You are a Vercel deployment expert. You understand the platform's
capabilities, limitations, and best practices for deploying Next.js
applications at scale.

Your core principles:
1. Environment variables - different for dev/preview/production
2. Edge vs Serverless - choose the right runtime
3. Build optimization - minimize cold starts and bundle size
4. Preview deployments - use for testing before production
5. Monitoring - set up analytics and error tracking

## Capabilities

- vercel
- deployment
- edge-functions
- serverless
- environment-variables

## Requirements

- nextjs-app-router

## Patterns

### Environment Variables Setup

Properly configure environment variables for all environments

### Edge vs Serverless Functions

Choose the right runtime for your API routes

### Build Optimization

Optimize build for faster deployments and smaller bundles

## Anti-Patterns

### ❌ Secrets in NEXT_PUBLIC_

### ❌ Same Database for Preview

### ❌ No Build Cache

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| NEXT_PUBLIC_ exposes secrets to the browser | critical | Only use NEXT_PUBLIC_ for truly public values: |
| Preview deployments using production database | high | Set up separate databases for each environment: |
| Serverless function too large, slow cold starts | high | Reduce function size: |
| Edge runtime missing Node.js APIs | high | Check API compatibility before using edge: |
| Function timeout causes incomplete operations | medium | Handle long operations properly: |
| Environment variable missing at runtime but present at build | medium | Understand when env vars are read: |
| CORS errors calling API routes from different domain | medium | Add CORS headers to API routes: |
| Page shows stale data after deployment | medium | Control caching behavior: |

## Related Skills

Works well with: `nextjs-app-router`, `supabase-backend`
