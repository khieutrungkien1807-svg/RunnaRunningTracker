# CONTAINERIZATION PATTERNS

> **Khi nào tải skill này:** Docker, Container, Kubernetes, K8s, Pod, Deployment

---

## DOCKERFILE BEST PRACTICES

**DOCKER-001.** Multi-stage builds for minimal images:
```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS runner
WORKDIR /app

# Don't run as root
RUN addgroup --system app && adduser --system --group app
USER app

COPY --from=builder --chown=app:app /app/dist ./dist
COPY --from=builder --chown=app:app /app/node_modules ./node_modules

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "dist/server.js"]
```

**DOCKER-002.** Layer caching optimization:
```dockerfile
# Copy dependency files first (rarely change)
COPY package*.json ./
RUN npm ci

# Then copy source (frequently changes)
COPY . .
RUN npm run build
```

**DOCKER-003.** Use .dockerignore:
```dockerignore
node_modules
npm-debug.log
.git
.gitignore
.env
.env.*
*.md
Dockerfile*
docker-compose*
.dockerignore
coverage
.nyc_output
dist
```

---

## DOCKER COMPOSE

**COMPOSE-001.** Development setup:
```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/node_modules  # Exclude node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## KUBERNETES BASICS

**K8S-001.** Deployment manifest:
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: myregistry/myapp:v1.0.0
          ports:
            - containerPort: 3000
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
          env:
            - name: NODE_ENV
              value: "production"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: myapp-secrets
                  key: database-url
```

**K8S-002.** Service manifest:
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP
---
# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - myapp.example.com
      secretName: myapp-tls
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 80
```

---

## SECRETS MANAGEMENT

**SECRET-001.** Kubernetes secrets:
```yaml
# secrets.yaml (apply with kubectl, not in git!)
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
type: Opaque
stringData:
  database-url: "postgresql://user:pass@db:5432/myapp"
  jwt-secret: "your-jwt-secret"
```

```bash
# Create secret from env file
kubectl create secret generic myapp-secrets \
  --from-env-file=.env.production
```

**SECRET-002.** External secrets (with External Secrets Operator):
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: myapp-secrets
  data:
    - secretKey: database-url
      remoteRef:
        key: myapp/production
        property: DATABASE_URL
```

---

## HEALTH CHECKS

**HEALTH-001.** Implement health endpoints:
```typescript
// Liveness - is the app alive?
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Readiness - can the app serve traffic?
app.get('/ready', async (req, res) => {
  try {
    // Check dependencies
    await prisma.$queryRaw`SELECT 1`;
    await redis.ping();

    res.status(200).json({ status: 'ready' });
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      error: error.message,
    });
  }
});
```

---

## RESOURCE LIMITS

**RESOURCE-001.** Set appropriate limits:
```yaml
resources:
  requests:
    memory: "128Mi"   # Guaranteed memory
    cpu: "100m"       # 0.1 CPU core
  limits:
    memory: "256Mi"   # Max memory (OOMKilled if exceeded)
    cpu: "500m"       # Max CPU (throttled if exceeded)
```

**RESOURCE-002.** Horizontal Pod Autoscaler:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## QUICK REFERENCE

| Concept | Docker | Kubernetes |
|---------|--------|------------|
| App unit | Container | Pod |
| Scaling | docker-compose scale | Deployment replicas |
| Networking | docker network | Service |
| Storage | volumes | PersistentVolumeClaim |
| Config | env_file | ConfigMap |
| Secrets | secrets | Secret |
| Load balancing | - | Service + Ingress |
