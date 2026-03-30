# OBSERVABILITY PATTERNS

> **Khi nào tải skill này:** Monitoring, Logging, Metrics, Observability, Tracing, Alert

---

## THREE PILLARS

**OBS-001.** Logs, Metrics, Traces:
```
LOGS    → What happened (events)
METRICS → How much/many (numbers)
TRACES  → Request journey (distributed)
```

---

## STRUCTURED LOGGING

**LOG-001.** Use structured logs:
```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: 'api-server',
    env: process.env.NODE_ENV,
  },
});

// Usage
logger.info({
  event: 'user_login',
  userId: user.id,
  method: 'oauth',
  duration: 234,
}, 'User logged in successfully');

// Output (JSON):
// {"level":"info","time":1704067200000,"service":"api-server","event":"user_login","userId":"abc123","method":"oauth","duration":234,"msg":"User logged in successfully"}
```

**LOG-002.** Request logging middleware:
```typescript
import { randomUUID } from 'crypto';

function requestLogger(req: Request, res: Response, next: NextFunction) {
  const requestId = req.headers['x-request-id'] || randomUUID();
  const startTime = Date.now();

  // Attach to request
  req.requestId = requestId;
  req.log = logger.child({ requestId });

  res.on('finish', () => {
    const duration = Date.now() - startTime;

    req.log.info({
      event: 'http_request',
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration,
      userAgent: req.headers['user-agent'],
    });
  });

  next();
}
```

---

## METRICS

**METRIC-001.** Prometheus metrics:
```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

// Request counter
const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
  registers: [registry],
});

// Request duration
const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'path'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5],
  registers: [registry],
});

// Active connections
const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  registers: [registry],
});

// Middleware
function metricsMiddleware(req: Request, res: Response, next: NextFunction) {
  const start = Date.now();

  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const path = req.route?.path || req.path;

    httpRequestsTotal.inc({
      method: req.method,
      path,
      status: res.statusCode,
    });

    httpRequestDuration.observe({ method: req.method, path }, duration);
  });

  next();
}

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.end(await registry.metrics());
});
```

---

## DISTRIBUTED TRACING

**TRACE-001.** OpenTelemetry setup:
```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

const sdk = new NodeSDK({
  serviceName: 'api-server',
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTLP_ENDPOINT,
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

**TRACE-002.** Manual span creation:
```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('api-server');

async function processOrder(order: Order) {
  return tracer.startActiveSpan('processOrder', async (span) => {
    try {
      span.setAttribute('order.id', order.id);
      span.setAttribute('order.total', order.total);

      // Child span
      await tracer.startActiveSpan('validateOrder', async (childSpan) => {
        await validateOrder(order);
        childSpan.end();
      });

      await tracer.startActiveSpan('processPayment', async (childSpan) => {
        await processPayment(order);
        childSpan.end();
      });

      span.setStatus({ code: SpanStatusCode.OK });
      return order;
    } catch (error) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

---

## ALERTING

**ALERT-001.** Define SLIs/SLOs:
```yaml
# Service Level Indicators (SLIs)
- Availability: % of successful requests
- Latency: p99 response time
- Error Rate: % of 5xx responses

# Service Level Objectives (SLOs)
- Availability: 99.9% (43 min downtime/month)
- Latency p99: < 200ms
- Error Rate: < 0.1%
```

**ALERT-002.** Prometheus alerting rules:
```yaml
# alerts.yml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: SlowResponses
        expr: |
          histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times"
          description: "p99 latency is {{ $value }}s"
```

---

## HEALTH CHECKS

**HEALTH-001.** Comprehensive health endpoint:
```typescript
interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, {
    status: 'pass' | 'fail';
    latency?: number;
    message?: string;
  }>;
}

app.get('/health', async (req, res) => {
  const checks: HealthCheck['checks'] = {};

  // Database
  try {
    const start = Date.now();
    await prisma.$queryRaw`SELECT 1`;
    checks.database = { status: 'pass', latency: Date.now() - start };
  } catch (error) {
    checks.database = { status: 'fail', message: error.message };
  }

  // Redis
  try {
    const start = Date.now();
    await redis.ping();
    checks.redis = { status: 'pass', latency: Date.now() - start };
  } catch (error) {
    checks.redis = { status: 'fail', message: error.message };
  }

  // External API
  try {
    const start = Date.now();
    await fetch(process.env.EXTERNAL_API_URL + '/health', {
      signal: AbortSignal.timeout(5000),
    });
    checks.externalApi = { status: 'pass', latency: Date.now() - start };
  } catch (error) {
    checks.externalApi = { status: 'fail', message: error.message };
  }

  const allPassing = Object.values(checks).every(c => c.status === 'pass');
  const status = allPassing ? 'healthy' : 'degraded';

  res.status(allPassing ? 200 : 503).json({ status, checks });
});
```

---

## QUICK REFERENCE

| Tool | Purpose |
|------|---------|
| Pino/Winston | Structured logging |
| Prometheus | Metrics collection |
| Grafana | Visualization |
| Jaeger/Tempo | Distributed tracing |
| OpenTelemetry | Unified observability |
| PagerDuty/OpsGenie | Alerting |

| Metric Type | Use Case |
|-------------|----------|
| Counter | Total requests, errors |
| Gauge | Active connections, queue size |
| Histogram | Request duration, response size |
| Summary | Similar to histogram, pre-calculated |
