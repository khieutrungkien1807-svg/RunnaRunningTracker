# CRYPTOGRAPHY PATTERNS

> **Khi nào tải skill này:** Encryption, Hashing, Crypto, Secret, Password, Key

---

## HASHING

**HASH-001.** Password hashing with Argon2:
```typescript
import { hash, verify } from '@node-rs/argon2';

const ARGON2_OPTIONS = {
  memoryCost: 65536,   // 64 MB
  timeCost: 3,         // iterations
  parallelism: 4,      // threads
};

async function hashPassword(password: string): Promise<string> {
  return hash(password, ARGON2_OPTIONS);
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  try {
    return await verify(hash, password);
  } catch {
    return false;
  }
}
```

**HASH-002.** Data integrity hashing:
```typescript
import { createHash } from 'crypto';

function sha256(data: string | Buffer): string {
  return createHash('sha256').update(data).digest('hex');
}

function sha256Base64(data: string | Buffer): string {
  return createHash('sha256').update(data).digest('base64');
}

// HMAC for authenticated hashing
function hmacSha256(data: string, secret: string): string {
  return createHmac('sha256', secret).update(data).digest('hex');
}
```

---

## ENCRYPTION

**ENCRYPT-001.** AES-256-GCM encryption:
```typescript
import { randomBytes, createCipheriv, createDecipheriv } from 'crypto';

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 12;
const TAG_LENGTH = 16;

function encrypt(plaintext: string, key: Buffer): string {
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv(ALGORITHM, key, iv);

  const encrypted = Buffer.concat([
    cipher.update(plaintext, 'utf8'),
    cipher.final(),
  ]);

  const tag = cipher.getAuthTag();

  // iv + tag + encrypted
  return Buffer.concat([iv, tag, encrypted]).toString('base64');
}

function decrypt(ciphertext: string, key: Buffer): string {
  const data = Buffer.from(ciphertext, 'base64');

  const iv = data.subarray(0, IV_LENGTH);
  const tag = data.subarray(IV_LENGTH, IV_LENGTH + TAG_LENGTH);
  const encrypted = data.subarray(IV_LENGTH + TAG_LENGTH);

  const decipher = createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(tag);

  return Buffer.concat([
    decipher.update(encrypted),
    decipher.final(),
  ]).toString('utf8');
}
```

**ENCRYPT-002.** Key derivation:
```typescript
import { scrypt, randomBytes } from 'crypto';
import { promisify } from 'util';

const scryptAsync = promisify(scrypt);

async function deriveKey(password: string, salt: Buffer): Promise<Buffer> {
  return scryptAsync(password, salt, 32) as Promise<Buffer>;
}

// Usage
const salt = randomBytes(16);
const key = await deriveKey(userPassword, salt);
const encrypted = encrypt(data, key);

// Store: salt + encrypted
```

---

## SECURE RANDOM

**RANDOM-001.** Generate secure tokens:
```typescript
import { randomBytes, randomUUID } from 'crypto';

// Random hex token
function generateToken(bytes = 32): string {
  return randomBytes(bytes).toString('hex');
}

// URL-safe token
function generateUrlSafeToken(bytes = 32): string {
  return randomBytes(bytes)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// UUID v4
function generateId(): string {
  return randomUUID();
}

// Short ID (for URLs)
import { nanoid } from 'nanoid';
const shortId = nanoid(10); // "V1StGXR8_Z"
```

---

## KEY MANAGEMENT

**KEY-001.** Environment-based key storage:
```typescript
// Load encryption key from environment
function getEncryptionKey(): Buffer {
  const keyHex = process.env.ENCRYPTION_KEY;

  if (!keyHex || keyHex.length !== 64) {
    throw new Error('Invalid ENCRYPTION_KEY: must be 64 hex characters (32 bytes)');
  }

  return Buffer.from(keyHex, 'hex');
}

// Generate new key
// openssl rand -hex 32
```

**KEY-002.** Key rotation:
```typescript
interface EncryptedData {
  keyId: string;  // Which key version
  data: string;   // Encrypted content
}

class KeyManager {
  private keys: Map<string, Buffer>;
  private currentKeyId: string;

  encrypt(plaintext: string): EncryptedData {
    return {
      keyId: this.currentKeyId,
      data: encrypt(plaintext, this.keys.get(this.currentKeyId)!),
    };
  }

  decrypt(encrypted: EncryptedData): string {
    const key = this.keys.get(encrypted.keyId);
    if (!key) {
      throw new Error(`Unknown key version: ${encrypted.keyId}`);
    }
    return decrypt(encrypted.data, key);
  }
}
```

---

## SIGNATURES

**SIG-001.** HMAC signatures:
```typescript
import { createHmac, timingSafeEqual } from 'crypto';

function sign(data: string, secret: string): string {
  return createHmac('sha256', secret).update(data).digest('hex');
}

function verifySignature(
  data: string,
  signature: string,
  secret: string
): boolean {
  const expected = sign(data, secret);

  // Timing-safe comparison
  if (signature.length !== expected.length) {
    return false;
  }

  return timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Usage: Webhook verification
function verifyWebhook(payload: string, signature: string): boolean {
  return verifySignature(payload, signature, process.env.WEBHOOK_SECRET!);
}
```

**SIG-002.** Asymmetric signatures (RSA/Ed25519):
```typescript
import { generateKeyPairSync, sign, verify } from 'crypto';

// Generate key pair
const { publicKey, privateKey } = generateKeyPairSync('ed25519');

// Sign
function signData(data: string): string {
  return sign(null, Buffer.from(data), privateKey).toString('base64');
}

// Verify
function verifyData(data: string, signature: string): boolean {
  return verify(
    null,
    Buffer.from(data),
    publicKey,
    Buffer.from(signature, 'base64')
  );
}
```

---

## COMMON MISTAKES

**AVOID-001.** Security anti-patterns:
```typescript
// BAD - ECB mode (patterns visible)
createCipheriv('aes-256-ecb', key, null);

// BAD - Predictable IV
const iv = Buffer.alloc(16, 0);  // All zeros!

// BAD - String comparison (timing attack)
if (signature === expected) { }

// BAD - MD5/SHA1 for passwords
createHash('md5').update(password);

// BAD - Weak random
Math.random().toString(36);

// GOOD alternatives shown above
```

---

## QUICK REFERENCE

| Algorithm | Use Case |
|-----------|----------|
| Argon2id | Password hashing |
| bcrypt | Password hashing (legacy) |
| SHA-256 | Data integrity |
| HMAC-SHA256 | Message authentication |
| AES-256-GCM | Symmetric encryption |
| X25519 | Key exchange |
| Ed25519 | Digital signatures |
| RSA-OAEP | Asymmetric encryption |

| Term | Meaning |
|------|---------|
| Salt | Random data added to input |
| IV/Nonce | Initialization vector (unique per message) |
| Tag | Authentication tag (GCM) |
| KDF | Key derivation function |
