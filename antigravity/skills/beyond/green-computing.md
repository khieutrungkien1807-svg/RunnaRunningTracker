# GREEN COMPUTING & CARBON-AWARE SCHEDULING

> **Tier:** 3-4 (Advanced/Deep)
> **Tags:** `[Green Computing, Carbon-Aware, Energy, Sustainability, Power]`
> **Khi nào dùng:** Tối ưu tiêu thụ điện năng, carbon-aware workloads, battery optimization

---

## OVERVIEW

Ngách tối ưu hóa phần mềm để:
- Tiêu thụ ít điện năng nhất
- Tự động dịch chuyển tính toán đến data center có năng lượng tái tạo
- Kéo dài thời lượng pin thiết bị di động
- Giảm carbon footprint của hệ thống

---

## ENERGY-PROPORTIONAL PROCESSING

**ENERGY-001.** Auto-scale services based on load:
```typescript
// Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5min before scaling down
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

**ENERGY-002.** Implement idle timeout for services:
```typescript
// Auto-shutdown idle services
class EnergyAwareService {
  private idleTimeout: NodeJS.Timeout | null = null;
  private readonly IDLE_DURATION = 5 * 60 * 1000; // 5 minutes

  async handleRequest(req: Request) {
    this.resetIdleTimer();
    return this.processRequest(req);
  }

  private resetIdleTimer() {
    if (this.idleTimeout) {
      clearTimeout(this.idleTimeout);
    }

    this.idleTimeout = setTimeout(() => {
      this.shutdown();
    }, this.IDLE_DURATION);
  }

  private async shutdown() {
    console.log('Service idle - shutting down to save energy');
    // Graceful shutdown
    await this.cleanup();
    process.exit(0);
  }
}
```

---

## CARBON-AWARE WORKLOADS

**CARBON-001.** Query carbon intensity API:
```typescript
import axios from 'axios';

interface CarbonIntensity {
  location: string;
  carbonIntensity: number; // gCO2/kWh
  timestamp: string;
}

async function getCarbonIntensity(location: string): Promise<CarbonIntensity> {
  // Use WattTime API, ElectricityMap API, or similar
  const response = await axios.get(
    `https://api.electricitymap.org/v3/carbon-intensity/latest`,
    {
      params: { zone: location },
      headers: { 'auth-token': process.env.ELECTRICITY_MAP_TOKEN },
    }
  );

  return {
    location,
    carbonIntensity: response.data.carbonIntensity,
    timestamp: response.data.datetime,
  };
}
```

**CARBON-002.** Schedule workloads during low-carbon periods:
```typescript
class CarbonAwareScheduler {
  async scheduleJob(job: Job) {
    const regions = ['us-west', 'eu-west', 'asia-east'];

    // Get carbon intensity for all regions
    const intensities = await Promise.all(
      regions.map(r => getCarbonIntensity(r))
    );

    // Find region with lowest carbon intensity
    const bestRegion = intensities.reduce((min, curr) =>
      curr.carbonIntensity < min.carbonIntensity ? curr : min
    );

    console.log(`Scheduling job in ${bestRegion.location} (${bestRegion.carbonIntensity} gCO2/kWh)`);

    // Route job to that region
    await this.executeInRegion(job, bestRegion.location);
  }

  async scheduleDeferrableJob(job: Job, deadline: Date) {
    // For non-urgent jobs, wait for low-carbon period
    const checkInterval = 30 * 60 * 1000; // Check every 30 minutes

    const interval = setInterval(async () => {
      const intensity = await getCarbonIntensity('current-region');

      // Execute if carbon intensity is low OR deadline approaching
      if (intensity.carbonIntensity < 200 || Date.now() > deadline.getTime()) {
        clearInterval(interval);
        await this.executeJob(job);
      }
    }, checkInterval);
  }
}
```

**CARBON-003.** Defer background tasks to low-carbon periods:
```typescript
// Example: Video encoding, ML training, data processing
class BackgroundTaskScheduler {
  async scheduleVideoEncoding(videoId: string) {
    const job = {
      type: 'video-encoding',
      videoId,
      priority: 'low',
      deadline: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
    };

    // Check if current carbon intensity is low
    const intensity = await getCarbonIntensity('current-region');

    if (intensity.carbonIntensity < 150) {
      // Low carbon - execute now
      await this.encodeVideo(videoId);
    } else {
      // High carbon - defer to queue
      await this.queueForLowCarbonPeriod(job);
    }
  }

  private async queueForLowCarbonPeriod(job: Job) {
    // Add to Redis queue with carbon-aware scheduler
    await redis.zadd(
      'carbon-aware-queue',
      job.deadline.getTime(),
      JSON.stringify(job)
    );
  }
}
```

---

## BATTERY-OPTIMIZED MOBILE SYNC

**BATTERY-001.** Batch network requests:
```typescript
// ❌ WRONG - Multiple individual requests
async function syncData() {
  await fetch('/api/user');
  await fetch('/api/posts');
  await fetch('/api/notifications');
  await fetch('/api/messages');
  // Each request wakes up radio - drains battery
}

// ✅ CORRECT - Single batched request
async function syncDataBatched() {
  const response = await fetch('/api/sync', {
    method: 'POST',
    body: JSON.stringify({
      resources: ['user', 'posts', 'notifications', 'messages'],
    }),
  });

  const data = await response.json();
  // Radio wakes once - saves battery
  return data;
}
```

**BATTERY-002.** Use exponential backoff for sync:
```typescript
class BatteryAwareSync {
  private syncInterval = 60 * 1000; // Start with 1 minute
  private readonly MAX_INTERVAL = 30 * 60 * 1000; // Max 30 minutes

  async startSync() {
    while (true) {
      try {
        await this.syncData();

        // Success - reset interval
        this.syncInterval = 60 * 1000;
      } catch (error) {
        // Failure - exponential backoff
        this.syncInterval = Math.min(
          this.syncInterval * 2,
          this.MAX_INTERVAL
        );
      }

      await this.sleep(this.syncInterval);
    }
  }

  private async syncData() {
    // Check battery level before sync
    if ('getBattery' in navigator) {
      const battery = await (navigator as any).getBattery();

      if (battery.level < 0.2 && !battery.charging) {
        // Low battery - skip non-critical sync
        console.log('Low battery - skipping sync');
        return;
      }
    }

    // Perform sync
    await fetch('/api/sync');
  }
}
```

**BATTERY-003.** Adapt behavior based on battery state:
```typescript
class AdaptiveBehavior {
  async initialize() {
    if ('getBattery' in navigator) {
      const battery = await (navigator as any).getBattery();

      // Adjust behavior based on battery
      if (battery.level < 0.2) {
        this.enablePowerSavingMode();
      }

      // Listen for battery changes
      battery.addEventListener('levelchange', () => {
        if (battery.level < 0.2) {
          this.enablePowerSavingMode();
        } else if (battery.level > 0.5) {
          this.disablePowerSavingMode();
        }
      });

      battery.addEventListener('chargingchange', () => {
        if (battery.charging) {
          this.enableFullFeatures();
        }
      });
    }
  }

  private enablePowerSavingMode() {
    // Reduce animation
    document.body.classList.add('power-saving');

    // Reduce sync frequency
    this.syncInterval = 10 * 60 * 1000; // 10 minutes

    // Disable auto-play videos
    this.disableAutoPlay();
  }
}
```

---

## CPU POWER MANAGEMENT

**CPU-001.** Use CPU frequency scaling:
```bash
# Linux - cpufreq governor
# Performance: Max frequency always
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Powersave: Min frequency always
echo powersave > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Ondemand: Dynamic scaling based on load
echo ondemand > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Schedutil: Scheduler-driven (recommended)
echo schedutil > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

**CPU-002.** Implement CPU sleep states:
```c
#include <unistd.h>

// Allow CPU to enter deep sleep when idle
void energy_efficient_wait() {
    // ❌ WRONG - Busy wait (100% CPU)
    while (!condition) {
        // Spin - wastes energy
    }

    // ✅ CORRECT - Sleep (CPU can enter low-power state)
    while (!condition) {
        usleep(1000); // Sleep 1ms - CPU enters C-state
    }
}
```

---

## MONITORING & MEASUREMENT

**MONITOR-001.** Measure power consumption:
```typescript
// Use Performance API (Chrome)
if ('measureUserAgentSpecificMemory' in performance) {
  const memory = await (performance as any).measureUserAgentSpecificMemory();
  console.log('Memory usage:', memory.bytes);
}

// Server-side: Use RAPL (Running Average Power Limit)
// Linux: /sys/class/powercap/intel-rapl/
```

**MONITOR-002.** Track carbon emissions:
```typescript
interface EnergyMetrics {
  cpuEnergyJoules: number;
  gpuEnergyJoules: number;
  durationSeconds: number;
  carbonIntensity: number; // gCO2/kWh
}

function calculateCarbonEmissions(metrics: EnergyMetrics): number {
  const totalEnergyKWh =
    (metrics.cpuEnergyJoules + metrics.gpuEnergyJoules) / 3600000;

  const carbonGrams = totalEnergyKWh * metrics.carbonIntensity;

  return carbonGrams;
}

// Log to monitoring system
await logMetric('carbon_emissions_grams', carbonGrams, {
  service: 'ml-training',
  region: 'us-west',
});
```

---

## AI LEVERAGE

**AI-001.** AI can help with:
- Analyze power consumption patterns
- Predict optimal times for workload execution
- Generate carbon-aware scheduling policies
- Optimize code for energy efficiency
- Suggest battery-saving strategies

**AI-002.** Example prompt:
```
"Analyze this function and suggest optimizations to reduce energy consumption:
[paste code]

Consider:
- CPU cycles
- Memory access patterns
- Network requests
- Algorithm complexity"
```

---

## QUICK REFERENCE

| Strategy | Energy Savings |
|----------|----------------|
| Batch network requests | 30-50% mobile battery |
| Auto-scale services | 40-60% server power |
| Carbon-aware scheduling | 20-40% carbon emissions |
| CPU frequency scaling | 10-30% CPU power |
| Exponential backoff | 20-40% mobile battery |

---

## BEST PRACTICES

**DO:**
- ✅ Batch network requests
- ✅ Use exponential backoff
- ✅ Implement auto-scaling
- ✅ Schedule deferrable workloads during low-carbon periods
- ✅ Monitor and measure energy consumption

**DON'T:**
- ❌ Busy-wait loops
- ❌ Frequent small network requests
- ❌ Run background tasks during high-carbon periods
- ❌ Ignore battery state on mobile
- ❌ Keep services running when idle

---

**Related Skills:**
- `beyond/exascale-computing.md` - HPC optimization
- `devops/cloud-services.md` - Cloud auto-scaling
- `frontend/web-performance.md` - Frontend optimization

**Version:** 1.0.0
**Last Updated:** 2024-01-15
