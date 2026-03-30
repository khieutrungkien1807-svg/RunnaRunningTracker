# Phase 1 Final Safety Layer - Reality Check

> **Date:** 2026-03-26
> **Issue:** Property tests mismatch với implementation thực tế

---

## Vấn đề phát hiện

Khi viết property tests cho HybridRetriever, tôi phát hiện:

1. **API Mismatch:** Tests giả định có `_calculate_score()` method, nhưng HybridRetriever thực tế dùng `retrieve()` trả về `RankedSkill`

2. **Complexity Mismatch:** HybridRetriever hiện tại đã rất phức tạp (BM25 + embeddings + contextual retrieval), property tests cần match với complexity này

3. **Dependencies:** Cần `rank-bm25` và `sentence-transformers` để test đầy đủ

---

## Quyết định

Thay vì viết property tests cho API không tồn tại, tôi sẽ:

### Option A: Simplify Tests (RECOMMENDED)
Test những invariants thực sự quan trọng với API hiện tại:

1. **Monotonicity:** `retrieve()` trả về results sorted by `final_score` descending
2. **Stability:** Small query change → similar top-k results
3. **Filter Correctness:** `top_k` parameter respected
4. **Diversity:** Results không collapse về 1 domain

### Option B: Add Missing Methods
Thêm `_calculate_score()` public method vào HybridRetriever để support property testing

### Option C: Skip Property Tests
Chấp nhận rằng HybridRetriever đã có unit tests đầy đủ, không cần property tests

---

## Recommendation

**Chọn Option A** vì:
- Tests match với production API
- Không cần thay đổi implementation
- Vẫn test được critical properties
- Practical và maintainable

---

## Next Steps

1. Rewrite property tests để dùng `retrieve()` API
2. Test với real SkillDocuments (không mock)
3. Focus vào end-to-end properties, không phải internal methods

---

**Decision:** Proceed with Option A
