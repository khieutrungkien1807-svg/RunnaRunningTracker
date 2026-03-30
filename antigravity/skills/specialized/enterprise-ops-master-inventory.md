# 🏢 ENTERPRISE GOVERNANCE & OPERATIONS — MASTER INVENTORY (v4.0.0)

> **Chuyên mục:** EA, EB, EC, ED, EE, EF, EG, EH, EI, EJ, EK, EL
> **Mục tiêu:** Biến App/Web thành Nền tảng Sinh thái, chống chịu thảm họa, vận hành 24/7

---

## 📋 Table of Contents

- [EA — Extensibility & Platform Architecture](#ea)
- [EB — Enterprise Security & SecOps](#eb)
- [EC — Observability, SRE & FinOps](#ec)
- [ED — Backoffice, Governance & Internal Tools](#ed)
- [EE — Legacy Modernization & Brownfield](#ee)
- [EF — Responsible AI & Algorithmic Ethics](#ef)
- [EG — Cognitive Ergonomics & Hyper-Accessibility](#eg)
- [EH — Doomsday Resilience & Air-Gapped Recovery](#eh)
- [EI — Agentic Web & Generative Interfaces](#ei)
- [EJ — TinyML & Micro-Edge Computing](#ej)
- [EK — DePIN & Tokenized Physical Infrastructure](#ek)
- [EL — Digital Twins & Modern Logistics](#el)

---

<a id="ea"></a>
## 🧩 EA: EXTENSIBILITY & PLATFORM ARCHITECTURE
*Biến App/Web của bạn thành một nền tảng để người khác (Third-party) có thể viết plugin, extension hoặc tích hợp vào hệ thống của họ.*

### Rule 1: Plugin Sandboxing (Cô lập mã độc)
Nếu bạn cho phép user cài Plugin/Extension vào hệ thống của bạn, **TUYỆT ĐỐI không cho chạy code trực tiếp**. Bắt buộc phải bọc (sandbox) code của bên thứ 3 trong WebAssembly (WASM) hoặc IFrame có cờ `sandbox` nghiêm ngặt để họ không thể đánh cắp Cookie/Token của hệ thống gốc.

```javascript
// Ví dụ: Sandbox Plugin trong IFrame an toàn
const iframe = document.createElement('iframe');
iframe.setAttribute('sandbox', 'allow-scripts'); // Chỉ cho script, cấm cookies/localStorage
iframe.src = 'plugin-runner.html';
document.body.appendChild(iframe);

// Giao tiếp qua postMessage có signature
window.addEventListener('message', (event) => {
  if (event.origin !== 'https://trusted-plugin.com') return; // Whitelist origin
  const { action, data, signature } = event.data;
  if (!verifyHMAC(data, signature, SECRET)) return; // Verify HMAC
  handlePluginAction(action, data);
});
```

### Rule 2: Webhook Delivery Guarantees (Đảm bảo giao nhận Webhook)
Khi hệ thống của bạn gửi sự kiện (Event) cho app khác, phải có cơ chế **Exponential Backoff** nếu server bên kia sập. Bắt buộc đính kèm `X-Signature-256` HMAC để đối tác xác thực dữ liệu.

```javascript
// Webhook gửi với retry exponential backoff
async function deliverWebhook(url, payload, secret, maxRetries = 5) {
  const body = JSON.stringify(payload);
  const signature = createHMACSignature(body, secret); // sha256 HMAC

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Signature-256': `sha256=${signature}`,
          'X-Delivery-Attempt': String(attempt),
        },
        body,
        signal: AbortSignal.timeout(10000), // 10s timeout
      });
      if (res.ok) return { success: true, attempt };
    } catch (err) {
      console.warn(`Webhook attempt ${attempt} failed: ${err.message}`);
    }
    // Exponential backoff: 2^attempt * 1000ms (max ~32s)
    await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
  }
  return { success: false, exhausted: true };
}
```

### Rule 3: API Versioning & Deprecation (Sunset Policy)
Không bao giờ sửa API đang chạy làm gãy app của khách hàng. Duy trì versioning và có quy trình "Hoàng hôn" (Sunset) cảnh báo trước **6 tháng**.

```javascript
// Middleware versioning tự động
app.use('/api', (req, res, next) => {
  const version = req.headers['api-version'] || 'v1';
  req.apiVersion = version;

  // Sunset header: cảnh báo khi dùng API cũ
  const deprecated = { v1: '2026-09-24', v2: '2027-03-24' };
  if (deprecated[version]) {
    res.set('Sunset', deprecated[version]);
    res.set('Deprecation', 'true');
    res.set('Link', `<https://api.example.com/${version}/docs>; rel="deprecation"`);
  }
  next();
});
```

---

<a id="eb"></a>
## 🛡️ EB: ENTERPRISE SECURITY & SecOps
*Bảo mật không chỉ là mã hóa mật khẩu. Đây là cách thiết lập lưới lửa bảo vệ tài sản số của bạn trước các cuộc tấn công có tổ chức.*

### Rule 1: Zero Trust & Context-Aware Access
Không tin tưởng bất cứ ai, kể cả nhân viên dùng mạng công ty. Quyền truy cập vào trang Admin phải được đánh giá theo thời gian thực dựa trên ngữ cảnh.

```typescript
// Context-Aware Access middleware
interface AccessContext {
  userId: string;
  ip: string;
  country: string;
  deviceFingerprint: string;
  mfaVerified: boolean;
  riskScore: number; // 0-100
}

async function evaluateAccess(ctx: AccessContext): Promise<'ALLOW' | 'MFA_REQUIRED' | 'BLOCK'> {
  const knownDevices = await getKnownDevices(ctx.userId);
  const allowedCountries = ['VN', 'SG', 'US'];

  // Chặn nếu đến từ quốc gia lạ
  if (!allowedCountries.includes(ctx.country)) {
    await alertSecurityTeam(`Login from unusual country: ${ctx.country}`);
    return 'BLOCK';
  }
  // Yêu cầu MFA nếu thiết bị lạ
  if (!knownDevices.includes(ctx.deviceFingerprint)) return 'MFA_REQUIRED';
  // Chặn nếu rủi ro cao
  if (ctx.riskScore > 80) return 'BLOCK';
  return 'ALLOW';
}
```

### Rule 2: Automated Secrets Rotation
Thông tin nhạy cảm (API Keys, Database Passwords) không bao giờ được lưu trong code hay file `.env` tĩnh. Bắt buộc dùng **HashiCorp Vault** hoặc **AWS Secrets Manager** để tự động đổi mật khẩu database mỗi 24 giờ.

```python
# Lấy secret động từ Vault thay vì .env
import hvac

def get_db_credentials():
    """Lấy credentials DB từ Vault, tự động renew."""
    client = hvac.Client(url='https://vault.internal:8200', token=VAULT_TOKEN)
    secret = client.secrets.database.generate_credentials(name='postgres-role')
    return {
        'username': secret['data']['username'],
        'password': secret['data']['password'],
        # Tự động hết hạn sau 24h theo Vault lease
    }
```

### Rule 3: Strict CSP & Extension Hardening
Content Security Policy (CSP) phải cấu hình cấm tuyệt đối `unsafe-inline` và `unsafe-eval`. Chỉ cho phép tải script/style từ các domain đã được whitelist.

```nginx
# nginx.conf - Strict CSP
add_header Content-Security-Policy "
  default-src 'self';
  script-src 'self' https://cdn.trusted.com;
  style-src 'self' https://fonts.googleapis.com;
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.example.com;
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
```

---

<a id="ec"></a>
## 📊 EC: OBSERVABILITY, SRE & FINOPS
*Bạn không thể quản lý thứ mà bạn không nhìn thấy. Đây là cách điều hành hệ thống 24/7 và kiểm soát hóa đơn server tiền tỷ.*

### Rule 1: The Three Pillars of Observability (OpenTelemetry)
Bắt buộc áp dụng OpenTelemetry. Mọi lỗi xảy ra phải liên kết được: **Metrics** (CPU/RAM) → **Logs** (Error detail) → **Traces** (Request flow qua Microservices).

```javascript
// OpenTelemetry setup cho Node.js
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';

const sdk = new NodeSDK({
  serviceName: 'my-service',
  traceExporter: new OTLPTraceExporter({ url: 'https://otel-collector:4318/v1/traces' }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({ url: 'https://otel-collector:4318/v1/metrics' }),
    exportIntervalMillis: 30_000,
  }),
});
sdk.start();
```

### Rule 2: Chaos Engineering & Auto-Remediation
Chủ động "phá" hệ thống (tắt ngẫu nhiên 1 server) trong giờ hành chính để xem hệ thống dự phòng có tự động bật lên không. Viết các kịch bản tự chữa lành.

```python
# Auto-remediation script: Xóa log cũ khi ổ đĩa đầy 90%
import shutil, subprocess

def check_and_remediate():
    total, used, free = shutil.disk_usage("/")
    usage_percent = (used / total) * 100
    if usage_percent > 90:
        # Tự động xóa log cũ hơn 7 ngày
        subprocess.run(["find", "/var/log", "-mtime", "+7", "-delete"])
        alert_ops(f"Disk {usage_percent:.1f}% full — auto-cleaned old logs.")
```

### Rule 3: FinOps Resource Tagging (Cost Anomaly Detection)
Mọi tài nguyên Cloud bắt buộc phải được dán nhãn (Tag) theo tính năng hoặc phòng ban. Nếu một tính năng đốt quá nhiều tiền server, hệ thống phải tự động cảnh báo.

```yaml
# Terraform resource với bắt buộc tagging
resource "aws_instance" "api_server" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.medium"
  tags = {
    Name        = "api-server-prod"
    Environment = "production"
    Team        = "backend"
    Feature     = "user-auth"
    CostCenter  = "engineering"
  }
}
```

---

<a id="ed"></a>
## 🏢 ED: BACKOFFICE, GOVERNANCE & INTERNAL TOOLS
*Cách xây dựng công cụ cho Đội ngũ CSKH, Kế toán, và Ban Giám đốc điều hành công ty mà không làm lộ dữ liệu người dùng.*

### Rule 1: ABAC over RBAC (Kiểm soát truy cập theo Thuộc tính)
Quyền truy cập không chỉ dựa trên Role mà phải dựa trên **Thuộc tính** (Attribute-Based Access Control).

```typescript
// ABAC Policy evaluation
interface AccessRequest {
  subject: { role: string; region: string; workingHours: boolean };
  resource: { ownerId: string; region: string };
  action: 'read' | 'write' | 'delete';
}

function evaluateABAC(request: AccessRequest): boolean {
  const { subject, resource, action } = request;
  // CSKH chỉ xem được khách hàng cùng khu vực, trong giờ làm việc
  if (subject.role === 'cskh') {
    return (
      action === 'read' &&
      subject.region === resource.region &&
      subject.workingHours === true
    );
  }
  return false;
}
```

### Rule 2: Maker-Checker Paradigm (Quy tắc 4 mắt)
Đối với các hành động nhạy cảm trong app Quản lý (như Hoàn tiền cho khách, Đổi cấu hình hệ thống), một người không thể tự làm từ đầu đến cuối. Người A tạo yêu cầu (Maker), Người B duyệt (Checker).

```typescript
// Maker-Checker workflow
type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

async function createRefundRequest(makerId: string, amount: number) {
  const request = await db.approvalRequests.create({
    data: { type: 'REFUND', amount, makerId, status: 'PENDING' }
  });
  await notifyApprovers(request.id); // Notify Checker team
  return { message: 'Waiting for approval', requestId: request.id };
}

async function approveRequest(checkerId: string, requestId: string) {
  const req = await db.approvalRequests.findUnique({ where: { id: requestId } });
  if (req.makerId === checkerId) throw new Error('Maker cannot approve own request');
  if (req.status !== 'PENDING') throw new Error('Already processed');
  await executeRefund(req); // Only runs after approval
  await db.approvalRequests.update({ where: { id: requestId }, data: { status: 'APPROVED', checkerId } });
}
```

### Rule 3: PII Data Masking by Default
Trên màn hình dashboard của nhân viên, dữ liệu PII như Số điện thoại, Email, Số thẻ tín dụng bắt buộc phải bị che đi (Masking). Chỉ khi được ghi log (Audit Trail) mới được bấm nút "Hiển thị".

```typescript
// PII Masking utilities
const maskPhone = (phone: string) => phone.replace(/(\d{2})\d+(\d{3})/, '$1*****$2');
// "+84 **** *** 123"

const maskEmail = (email: string) => {
  const [local, domain] = email.split('@');
  return `${local[0]}***@${domain}`;
};

const maskCard = (card: string) => `**** **** **** ${card.slice(-4)}`;

// Audit trail khi nhân viên yêu cầu xem full PII
async function revealPII(staffId: string, customerId: string, fieldName: string) {
  await auditLog.create({ staffId, customerId, fieldName, action: 'REVEAL_PII', timestamp: new Date() });
  return await getFullPII(customerId, fieldName);
}
```

---

<a id="ee"></a>
## 🕰️ EE: LEGACY MODERNIZATION & BROWNFIELD
*Trong thực tế, 80% công việc của các tập đoàn tỷ đô không phải là viết code mới (Greenfield), mà là tích hợp hoặc đập bỏ các hệ thống COBOL/Java cũ kỹ từ 20 năm trước mà không làm gián đoạn kinh doanh.*

### Rule 1: Strangler Fig Pattern (Mô hình Cây đa bóp cổ)
Cấm tuyệt đối chiến lược "Đập đi xây lại từ đầu" (Big Bang Rewrite). Bắt buộc phải xây dựng các API mới bọc bên ngoài hệ thống cũ.

```
BEFORE:                          AFTER (Strangler Fig):
Client → Legacy Monolith         Client → API Gateway
                                         ├─ /users → New Microservice
                                         ├─ /orders → New Microservice
                                         └─ /report → Legacy (still running)
```

### Rule 2: Anti-Corruption Layer (Lớp Chống tha hóa)
Khi Microservice mới phải nói chuyện với Database cục mịch từ năm 2005, bắt buộc phải xây một lớp "phiên dịch" (ACL) ở giữa.

```typescript
// Anti-Corruption Layer: Dịch dữ liệu Legacy → Domain Model mới
class LegacyCustomerACL {
  // Legacy DB trả về flat format cũ kỹ
  fromLegacy(legacyRecord: LegacyCustomerRecord): Customer {
    return {
      id: legacyRecord.CUST_ID,
      fullName: `${legacyRecord.FIRST_NM} ${legacyRecord.LAST_NM}`,
      email: legacyRecord.EMAIL_ADDR?.toLowerCase() ?? null,
      createdAt: this.parseLegacyDate(legacyRecord.CREATE_DT),
    };
  }
  // Không bao giờ để format cũ rò rỉ ra domain mới!
  private parseLegacyDate(dt: string): Date {
    return new Date(dt.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
  }
}
```

### Rule 3: Read-Only Replicas for Legacy DBs
Không bao giờ cho phép hệ thống mới ghi (write) trực tiếp vào cơ sở dữ liệu của hệ thống cũ. Chỉ đọc qua các bản sao (Replicas) hoặc đồng bộ qua Change Data Capture (CDC - như Debezium).

```yaml
# Debezium CDC config - đồng bộ 1 chiều từ Legacy MySQL → Kafka
connector.class: io.debezium.connector.mysql.MySqlConnector
database.hostname: legacy-mysql.internal
database.port: 3306
database.user: debezium_readonly
database.server.name: legacy_crm
table.include.list: legacy_crm.customers, legacy_crm.orders
transforms: unwrap
transforms.unwrap.type: io.debezium.transforms.ExtractNewRecordState
```

---

<a id="ef"></a>
## ⚖️ EF: RESPONSIBLE AI & ALGORITHMIC ETHICS
*Khi hệ thống của bạn (có tích hợp AI) bắt đầu đưa ra quyết định ảnh hưởng đến sinh mạng, tài chính, hoặc quyền lợi của con người.*

### Rule 1: Explainable AI (XAI) Mandate
Đối với các quyết định quan trọng (Y tế, Tài chính, Pháp lý), CẤM sử dụng các mô hình hộp đen (Black-box) mà không có lớp giải thích.

```python
import shap, xgboost

model = xgboost.XGBClassifier()
model.fit(X_train, y_train)

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Giải thích tại sao hồ sơ #42 bị từ chối vay vốn
def explain_decision(customer_idx: int) -> dict:
    feature_impacts = dict(zip(feature_names, shap_values[customer_idx]))
    top_reasons = sorted(feature_impacts.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    return {
        "decision": "REJECTED",
        "reasons": [{"factor": k, "impact": round(v, 2)} for k, v in top_reasons]
    }
# Output: "Bị từ chối vì: Điểm tín dụng thấp (-0.8), Nợ hiện tại cao (-0.5)"
```

### Rule 2: Algorithmic Bias Mitigation (Khử thiên kiến)
Dữ liệu nạp vào AI phải trải qua bộ lọc cân bằng. Nếu kết quả đầu ra bị thay đổi quá 5% khi thay đổi Giới tính/Sắc tộc, model đó không được phép deploy.

```python
def test_algorithmic_fairness(model, test_data: pd.DataFrame, threshold=0.05):
    """kiểm tra tính công bằng: Tỷ lệ approval giữa các nhóm không được chênh > 5%"""
    results = {}
    base_approval = model.predict(test_data).mean()
    for gender in ['male', 'female', 'non-binary']:
        subset = test_data.copy()
        subset['gender'] = gender  # Thay đổi thuộc tính nhạy cảm
        approval_rate = model.predict(subset).mean()
        delta = abs(approval_rate - base_approval)
        results[gender] = {'rate': approval_rate, 'delta': delta, 'fair': delta < threshold}
    return results
```

### Rule 3: Copyright & IP Sanitization
Mọi mô hình Generative AI tạo ra nội dung cho khách hàng phải đi qua màng lọc kiểm tra bản quyền hoặc gắn Thủy vân số (Watermarking).

---

<a id="eg"></a>
## 🧠 EG: COGNITIVE ERGONOMICS & HYPER-ACCESSIBILITY
*Thiết kế phần mềm phù hợp với giới hạn thần kinh của não người, phục vụ cả những người mắc chứng ADHD, tự kỷ, hoặc suy giảm nhận thức.*

### Rule 1: Hick's Law & Cognitive Load Limits
Số lượng lựa chọn trên một màn hình quyết định thời gian phản hồi của não bộ. Cấm nhồi nhét quá **7 (±2)** luồng thông tin trên cùng một view. Bắt buộc áp dụng Progressive Disclosure.

### Rule 2: Non-Relational Error Recovery
Khi người dùng thao tác sai, thông báo lỗi cấm dùng các từ ngữ kỹ thuật (Ví dụ: "Invalid payload 422"). Phải dùng ngôn ngữ chữa lành và đưa ra đúng 1 nút bấm (Call-to-Action) duy nhất để họ quay lại trạng thái an toàn.

```json
// ❌ Lỗi kỹ thuật gây hoang mang:
{ "error": "HTTP 422 Unprocessable Entity: Invalid payload schema" }

// ✅ Thông báo thân thiện:
{
  "message": "Có vẻ thông tin nhập chưa đúng. Bạn có muốn thử lại không?",
  "action": { "label": "Thử lại", "href": "/checkout" }
}
```

### Rule 3: Motor-Impairment Tolerances (Fitts's Law)
Các nút bấm thao tác nguy hiểm (Xóa tài khoản, Chuyển tiền) phải tuân thủ Fitts's Law (càng xa thì càng phải to) và có độ trễ (Debounce) tối thiểu **500ms** để chống việc người bị run tay click đúp vô ý.

---

<a id="eh"></a>
## 🌋 EH: DOOMSDAY RESILIENCE & AIR-GAPPED RECOVERY
*Chuẩn bị cho những ngày tồi tệ nhất: Datacenter bị cháy, toàn bộ hạ tầng AWS sập, hoặc công ty bị dính Ransomware mã hóa sạch toàn bộ cơ sở dữ liệu.*

### Rule 1: Immutable WORM Backups
Bản sao lưu cơ sở dữ liệu cốt lõi phải được lưu ở định dạng **WORM (Write Once, Read Many)**. Ngay cả tài khoản Super Admin hoặc Root cũng KHÔNG THỂ xóa hoặc ghi đè bản backup này trong vòng 30 ngày. Đây là cách duy nhất sống sót qua Ransomware.

```bash
# AWS S3 WORM Object Lock - không thể xóa trong 30 ngày
aws s3api put-object-lock-configuration \
  --bucket critical-backups-prod \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 30
      }
    }
  }'
```

### Rule 2: Multi-Region Active-Active Failover
Hệ thống phải chạy song song ở ít nhất 2 khu vực địa lý cách xa nhau (VD: Tokyo và Singapore). Nếu một Datacenter bị mất điện toàn phần, hệ thống định tuyến (Route53/Cloudflare) phải tự động bẻ 100% traffic sang khu vực còn lại trong **dưới 30 giây** mà người dùng không hề hay biết.

```hcl
# Terraform: Cloudflare Load Balancer Active-Active
resource "cloudflare_load_balancer" "global" {
  zone_id     = var.zone_id
  name        = "api.example.com"
  fallback_pool_id = cloudflare_load_balancer_pool.singapore.id
  default_pool_ids = [
    cloudflare_load_balancer_pool.tokyo.id,
    cloudflare_load_balancer_pool.singapore.id,
  ]
  steering_policy = "geo"
  session_affinity = "cookie"
}
```

### Rule 3: Air-Gapped Cold Storage & Glass-break Procedures
Phải có một luồng dữ liệu một chiều (Data Diode) đưa các thông tin sinh tử ra một máy chủ "lạnh" (Cold Storage) hoàn toàn ngắt kết nối vật lý với Internet. Quy trình "Đập kính khẩn cấp" (Glass-break) phải được lập trình sẵn bằng các script IaC (Terraform) để tự động dựng lại toàn bộ hạ tầng công ty từ số 0 chỉ với 1 cú click.

```bash
# Glass-break script: Khởi tạo lại toàn bộ hạ tầng từ 0
#!/bin/bash
set -euo pipefail
echo "🚨 GLASS-BREAK ACTIVATED — Rebuilding infrastructure..."
aws s3 cp s3://air-gapped-backup/latest/db.sql.gpg /tmp/ # Lấy backup từ Cold Storage
gpg --decrypt /tmp/db.sql.gpg | psql $PRIMARY_DB_URL     # Khôi phục DB
terraform -chdir=./infra apply -auto-approve              # Dựng lại servers
kubectl apply -f ./k8s/                                   # Deploy lại services
echo "✅ Infrastructure restored in $(date)."
```

---

<a id="ei"></a>
## 🤖 EI: AGENTIC WEB & GENERATIVE INTERFACES
*Web và App hiện đại không còn là những màn hình tĩnh chờ người dùng click. Chúng là các "Đại lý" (Agents) tự động suy nghĩ và thay đổi giao diện theo thời gian thực dựa trên ý định của người dùng.*

### Rule 1: Streaming UI & Server-Sent Events (SSE)
Không chờ AI hoặc Server xử lý xong toàn bộ mới trả về kết quả. Bắt buộc dùng SSE hoặc WebSockets để "stream" (truyền) từng mảnh giao diện (Component chunks) từ server xuống client.

```javascript
// Next.js App Router: Streaming Response từ AI
import { OpenAI } from 'openai';
export async function POST(req: Request) {
  const { message } = await req.json();
  const client = new OpenAI();
  const stream = client.beta.chat.completions.stream({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: message }],
  });
  // Trả về stream ngay lập tức — không đợi xử lý xong
  return new Response(stream.toReadableStream(), {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}
```

### Rule 2: Headless CMS & API-First Architecture
Từ bỏ hoàn toàn các hệ thống nguyên khối (Monolith). Mọi logic nội dung phải tách rời khỏi giao diện. Giao diện (Frontend) chỉ làm nhiệm vụ "hứng" data qua GraphQL hoặc RESTful API, cho phép một backend duy nhất phục vụ cả Web, iOS, Android và màn hình trên xe hơi.

### Rule 3: RAG-Driven State Management
Quản lý trạng thái (State) của App phải kết hợp với **Vector Database** lưu trữ ngữ cảnh ngắn hạn của người dùng, giúp AI trong App "nhớ" được người dùng vừa làm gì ở trang trước.

```typescript
// Lưu ngữ cảnh user vào Vector DB (Supabase pgvector)
async function saveUserContext(userId: string, action: string, embedding: number[]) {
  await supabase.from('user_context').upsert({
    user_id: userId,
    action_summary: action,
    embedding, // Vector embedding của hành động
    created_at: new Date().toISOString(),
  });
}
```

---

<a id="ej"></a>
## 🧠 EJ: TINYML & MICRO-EDGE COMPUTING
*Hiện đại hóa IoT không phải là kết nối chip với Cloud. Hiện đại là mang nguyên một mô hình Trí tuệ nhân tạo nhét thẳng vào những con vi điều khiển nhỏ bé đang chạy bằng pin.*

### Rule 1: Int8/Int4 Quantization (Lượng tử hóa mô hình)
Cấm chạy mô hình AI float32 trên vi điều khiển. Mọi mô hình phải được lượng tử hóa xuống số nguyên **8-bit hoặc 4-bit** qua TensorFlow Lite for Microcontrollers để vừa vặn với vài chục KB RAM.

```python
import tensorflow as tf

# Chuyển đổi model float32 → TFlite int8 cho MCU
converter = tf.lite.TFLiteConverter.from_saved_model('my_model')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.int8]
# Cần representative dataset để calibrate quantization
converter.representative_dataset = representative_data_gen
tflite_model = converter.convert()

with open('model_int8.tflite', 'wb') as f:
    f.write(tflite_model)
# Kích thước giảm từ ~4MB xuống ~500KB — phù hợp với STM32
```

### Rule 2: Wake-on-Event Architecture (Ngủ sâu & Thức thông minh)
MCU (Vi điều khiển) phải ở trạng thái "ngủ sâu" (Deep Sleep) 99% thời gian để tiết kiệm pin. Chỉ khi cảm biến gia tốc hoặc micrô phát hiện ngưỡng năng lượng bất thường (Hardware Interrupt), hệ thống mới thức dậy.

### Rule 3: Firmware Over-The-Air (FOTA) với Delta Updates
Khi cập nhật phần mềm cho hàng ngàn thiết bị IoT từ xa, không bao giờ gửi toàn bộ file nhị phân. Bắt buộc chỉ gửi "phần chênh lệch" (Delta Patch) giữa bản cũ và bản mới để tiết kiệm băng thông.

---

<a id="ek"></a>
## 🌐 EK: DePIN & TOKENIZED PHYSICAL INFRASTRUCTURE
*Sự kết hợp hiện đại nhất giữa Hệ thống, IoT, Kinh tế và Vận tải. Người dân tự mua thiết bị và kết nối thành một mạng lưới khổng lồ, được trả thưởng bằng token tự động.*

### Rule 1: Cryptographic Hardware Identity
Mỗi thiết bị IoT khi xuất xưởng phải được nhúng một khóa bảo mật bất biến (Secure Element) để ký (sign) mọi dữ liệu nó gửi lên mạng. Chống lại việc hacker giả lập dữ liệu bằng phần mềm để trục lợi điểm thưởng.

### Rule 2: Proof of Physical Work (PoPW)
Thuật toán Backend phải xác minh được thiết bị đó thực sự đang hoạt động ở thế giới thực. (Ví dụ: Đối chiếu dữ liệu GPS của thiết bị với dữ liệu trạm phát sóng viễn thông lân cận để xác nhận vị trí).

### Rule 3: Automated Micro-Transactions
Hệ thống kinh tế đằng sau phải xử lý hàng triệu giao dịch siêu nhỏ (Micro-payments) mỗi giây. Bắt buộc sử dụng kiến trúc **Blockchain Layer 2** hoặc **Directed Acyclic Graph (DAG)** không tốn phí gas (fee-less) để trả thưởng cho thiết bị theo thời gian thực.

---

<a id="el"></a>
## 🏙️ EL: DIGITAL TWINS & MODERN LOGISTICS
*Quản lý con người, dịch vụ và vận tải không còn nhìn trên các bảng tính Excel. Chúng được hiển thị dưới dạng bản đồ 3D thời gian thực (Digital Twins) phản chiếu chính xác 1:1 thế giới thực.*

### Rule 1: WebGL/WebGPU Spatial Rendering
Màn hình quản trị (Admin Dashboard) của các dịch vụ vận tải, y tế lớn phải render được mô hình 3D của bệnh viện, kho bãi hoặc thành phố ngay trên trình duyệt với WebGL. Dữ liệu xe cộ/bệnh nhân di chuyển phải update trên bản đồ 3D ở tốc độ **60fps**.

```javascript
// deck.gl — Render hàng ngàn xe/giao hàng trên bản đồ 3D, 60fps
import { Deck } from '@deck.gl/core';
import { ScenegraphLayer } from '@deck.gl/mesh-layers';

const layer = new ScenegraphLayer({
  id: 'delivery-fleet',
  data: liveVehicleData,        // WebSocket stream từ GPS tracker
  scenegraph: '/models/truck.glb',
  getPosition: d => [d.longitude, d.latitude, 0],
  getOrientation: d => [0, d.bearing, 90],
  updateTriggers: { getPosition: timestamp }, // Re-render khi có data mới
});
```

### Rule 2: Graph-based Routing Engines (Thuật toán Tìm đường Đồ thị)
Bài toán giao hàng hiện đại không chỉ tính khoảng cách (Distance). Thuật toán định tuyến (ví dụ dùng Neo4j hoặc pgRouting) phải tính trọng số dựa trên: Mật độ kẹt xe trực tiếp, thời gian chờ thang máy tại tòa nhà, và kích thước gói hàng có vừa cốp xe hay không.

```sql
-- pgRouting: Tìm đường tối ưu tính cả kẹt xe
SELECT * FROM pgr_dijkstra(
  'SELECT id, source, target,
   cost_seconds * traffic_multiplier AS cost  -- Điều chỉnh theo kẹt xe
   FROM road_network
   WHERE cargo_width < 2.5  -- Lọc đường hẻm quá nhỏ',
  start_node, end_node, directed := true
);
```

### Rule 3: Multi-Agent Orchestration (Điều phối Đa đặc vụ AI)
Trong một hệ thống dịch vụ phức tạp, thay vì viết các câu lệnh `if/else` chằng chịt, hãy triển khai các Agent AI nói chuyện với nhau.

```
Agent Kho (Inventory Agent):
  "Hết hàng SKU-123"
  → Agent Mua sắm (Procurement Agent):
      Tự động đàm phán giá với 3 nhà cung cấp qua API
      → Agent Vận tải (Logistics Agent):
          Book xe tải, tính tuyến đường tối ưu
          → Agent Tài chính (Finance Agent):
              Xử lý thanh toán tự động
```
