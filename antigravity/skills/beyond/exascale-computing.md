# EXASCALE COMPUTING & SUPERCOMPUTING

> **Tier:** 4 (Deep/System-level)
> **Tags:** `[Exascale, Supercomputing, MPI, HPC, Parallel, Cluster]`
> **Khi nào dùng:** Lập trình cho siêu máy tính, cụm 100,000+ CPU/GPU, mô phỏng khoa học

---

## OVERVIEW

Ngách viết phần mềm chạy trên cụm (cluster) gồm hàng chục ngàn CPU/GPU kết nối với nhau, phục vụ:
- Dự báo thời tiết toàn cầu
- Mô phỏng vụ nổ hạt nhân
- Train model AI khổng lồ (GPT-scale)
- Mô phỏng protein folding
- Computational fluid dynamics

---

## MPI (MESSAGE PASSING INTERFACE) STANDARDS

**MPI-001.** ALWAYS use MPI for inter-node communication:
```c
#include <mpi.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int world_size, world_rank;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    printf("Process %d of %d\n", world_rank, world_size);

    // Your parallel computation here

    MPI_Finalize();
    return 0;
}
```

**MPI-002.** Use non-blocking communication to avoid bottlenecks:
```c
// ❌ WRONG - Blocking (causes deadlock risk)
MPI_Send(send_buf, count, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD);
MPI_Recv(recv_buf, count, MPI_DOUBLE, source, tag, MPI_COMM_WORLD, &status);

// ✅ CORRECT - Non-blocking
MPI_Request send_req, recv_req;
MPI_Isend(send_buf, count, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD, &send_req);
MPI_Irecv(recv_buf, count, MPI_DOUBLE, source, tag, MPI_COMM_WORLD, &recv_req);

// Do computation while communication happens
compute_local_work();

// Wait for communication to complete
MPI_Wait(&send_req, MPI_STATUS_IGNORE);
MPI_Wait(&recv_req, MPI_STATUS_IGNORE);
```

**MPI-003.** Use collective operations for efficiency:
```c
// Broadcast data from root to all processes
MPI_Bcast(data, count, MPI_DOUBLE, root, MPI_COMM_WORLD);

// Gather data from all processes to root
MPI_Gather(send_buf, send_count, MPI_DOUBLE,
           recv_buf, recv_count, MPI_DOUBLE,
           root, MPI_COMM_WORLD);

// Reduce (sum, max, min) across all processes
MPI_Reduce(local_sum, global_sum, 1, MPI_DOUBLE,
           MPI_SUM, root, MPI_COMM_WORLD);

// All-to-all reduction (everyone gets result)
MPI_Allreduce(local_sum, global_sum, 1, MPI_DOUBLE,
              MPI_SUM, MPI_COMM_WORLD);
```

---

## MEMORY LOCALITY (NUMA)

**NUMA-001.** Pin threads to CPU cores near their memory:
```c
#include <numa.h>
#include <numaif.h>

// Check NUMA availability
if (numa_available() < 0) {
    fprintf(stderr, "NUMA not available\n");
    exit(1);
}

// Get number of NUMA nodes
int num_nodes = numa_num_configured_nodes();

// Allocate memory on specific NUMA node
void* mem = numa_alloc_onnode(size, node_id);

// Bind thread to specific NUMA node
numa_run_on_node(node_id);

// Free NUMA memory
numa_free(mem, size);
```

**NUMA-002.** Use first-touch policy for optimal placement:
```c
// Allocate memory
double* array = (double*)malloc(N * sizeof(double));

// Initialize in parallel - each thread touches its own chunk
#pragma omp parallel for
for (int i = 0; i < N; i++) {
    array[i] = 0.0;  // First touch - memory allocated on local node
}

// Now computation will be fast - data is local
#pragma omp parallel for
for (int i = 0; i < N; i++) {
    array[i] = compute(array[i]);
}
```

---

## JOB SCHEDULING (SLURM/PBS)

**SLURM-001.** Write efficient batch job scripts:
```bash
#!/bin/bash
#SBATCH --job-name=my_simulation
#SBATCH --nodes=100              # Number of nodes
#SBATCH --ntasks-per-node=48     # MPI tasks per node
#SBATCH --cpus-per-task=1        # Threads per MPI task
#SBATCH --time=24:00:00          # Max runtime (HH:MM:SS)
#SBATCH --partition=compute      # Queue/partition
#SBATCH --account=my_project     # Billing account
#SBATCH --output=job_%j.out      # Output file (%j = job ID)
#SBATCH --error=job_%j.err       # Error file

# Load modules
module load gcc/11.2.0
module load openmpi/4.1.2
module load hdf5/1.12.1

# Set environment
export OMP_NUM_THREADS=1
export MPI_BUFFER_SIZE=20000000

# Run MPI application
srun ./my_app input.dat
```

**SLURM-002.** Request appropriate resources:
```bash
# CPU-only job
#SBATCH --nodes=10
#SBATCH --ntasks-per-node=128

# GPU job
#SBATCH --nodes=4
#SBATCH --gres=gpu:4             # 4 GPUs per node
#SBATCH --ntasks-per-node=4      # 1 MPI task per GPU

# Large memory job
#SBATCH --mem=500GB              # Total memory per node
#SBATCH --constraint=highmem     # Request high-memory nodes
```

---

## PERFORMANCE OPTIMIZATION

**PERF-001.** Minimize communication overhead:
```c
// ❌ WRONG - Too many small messages
for (int i = 0; i < N; i++) {
    MPI_Send(&data[i], 1, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD);
}

// ✅ CORRECT - One large message
MPI_Send(data, N, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD);
```

**PERF-002.** Overlap computation and communication:
```c
// Start non-blocking communication
MPI_Isend(boundary_data, size, MPI_DOUBLE, neighbor, tag,
          MPI_COMM_WORLD, &request);

// Compute interior points (don't need boundary data yet)
compute_interior();

// Wait for communication
MPI_Wait(&request, MPI_STATUS_IGNORE);

// Now compute boundary points
compute_boundary();
```

**PERF-003.** Use compiler auto-vectorization:
```c
// Enable auto-vectorization with compiler flags:
// GCC: -O3 -march=native -ftree-vectorize
// Intel: -O3 -xHost -qopt-report=5

// Write vectorizable loops
#pragma omp simd
for (int i = 0; i < N; i++) {
    c[i] = a[i] + b[i];  // Simple, vectorizable
}

// Avoid:
// - Function calls in loop
// - Conditional branches
// - Non-contiguous memory access
```

---

## LOAD BALANCING

**BALANCE-001.** Use dynamic scheduling for irregular workloads:
```c
#include <omp.h>

// Static scheduling - equal chunks (good for uniform work)
#pragma omp parallel for schedule(static)
for (int i = 0; i < N; i++) {
    uniform_work(i);
}

// Dynamic scheduling - work stealing (good for irregular work)
#pragma omp parallel for schedule(dynamic, chunk_size)
for (int i = 0; i < N; i++) {
    irregular_work(i);  // Some iterations take longer
}

// Guided scheduling - adaptive chunk size
#pragma omp parallel for schedule(guided)
for (int i = 0; i < N; i++) {
    adaptive_work(i);
}
```

---

## I/O OPTIMIZATION

**IO-001.** Use parallel I/O (HDF5, MPI-IO):
```c
#include <hdf5.h>

// Create file with parallel access
hid_t plist_id = H5Pcreate(H5P_FILE_ACCESS);
H5Pset_fapl_mpio(plist_id, MPI_COMM_WORLD, MPI_INFO_NULL);
hid_t file_id = H5Fcreate("output.h5", H5F_ACC_TRUNC,
                          H5P_DEFAULT, plist_id);

// Each process writes its own chunk
hid_t dset_id = H5Dcreate(file_id, "dataset", ...);
H5Dwrite(dset_id, H5T_NATIVE_DOUBLE, memspace, filespace,
         H5P_DEFAULT, local_data);

H5Dclose(dset_id);
H5Fclose(file_id);
```

---

## DEBUGGING & PROFILING

**DEBUG-001.** Use parallel debuggers:
```bash
# GDB with MPI
mpirun -np 4 xterm -e gdb ./my_app

# TotalView (commercial)
totalview mpirun -a -np 100 ./my_app

# ARM DDT (commercial)
ddt mpirun -np 100 ./my_app
```

**PROFILE-001.** Profile MPI applications:
```bash
# Intel VTune
mpirun -np 100 amplxe-cl -collect hotspots ./my_app

# Scalasca
scalasca -analyze mpirun -np 100 ./my_app

# TAU (Tuning and Analysis Utilities)
mpirun -np 100 tau_exec ./my_app
```

---

## FAULT TOLERANCE

**FAULT-001.** Implement checkpointing:
```c
// Checkpoint every N iterations
if (iteration % checkpoint_interval == 0) {
    // Each process saves its state
    char filename[256];
    sprintf(filename, "checkpoint_%d_rank_%d.dat", iteration, rank);

    FILE* fp = fopen(filename, "wb");
    fwrite(local_data, sizeof(double), local_size, fp);
    fclose(fp);

    // Synchronize
    MPI_Barrier(MPI_COMM_WORLD);
}
```

---

## AI LEVERAGE

**AI-001.** AI can help with:
- Generate MPI communication patterns
- Optimize domain decomposition
- Write Slurm job scripts
- Identify load imbalance
- Suggest vectorization opportunities
- Auto-tune parameters (chunk size, buffer size)

**AI-002.** Example prompt:
```
"Generate MPI code for 2D heat equation using domain decomposition.
Requirements:
- 1000x1000 grid
- Non-blocking communication
- Overlap computation and communication
- Use Jacobi iteration"
```

---

## QUICK REFERENCE

| Concept | Best Practice |
|---------|---------------|
| Communication | Non-blocking, collective ops |
| Memory | NUMA-aware, first-touch |
| Scheduling | Request exact resources needed |
| I/O | Parallel HDF5/MPI-IO |
| Debugging | Parallel debuggers (TotalView, DDT) |
| Profiling | VTune, Scalasca, TAU |

---

## COMMON PITFALLS

**AVOID-001.** Don't use too many MPI processes:
```
# ❌ WRONG - More processes than work
mpirun -np 10000 ./small_problem  # Only 100 data points

# ✅ CORRECT - Match processes to problem size
mpirun -np 100 ./small_problem
```

**AVOID-002.** Don't ignore load imbalance:
```c
// ❌ WRONG - Static partitioning for irregular work
int chunk = N / world_size;
int start = rank * chunk;
int end = (rank + 1) * chunk;

// ✅ CORRECT - Dynamic work distribution
#pragma omp parallel for schedule(dynamic)
for (int i = 0; i < N; i++) {
    irregular_work(i);
}
```

---

**Related Skills:**
- `deep-tech/gpu-computing.md` - GPU acceleration
- `deep-tech/compiler-tools.md` - Compiler optimization
- `beyond/green-computing.md` - Energy efficiency

**Version:** 1.0.0
**Last Updated:** 2024-01-15
