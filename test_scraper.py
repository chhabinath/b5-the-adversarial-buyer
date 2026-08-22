import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.scraper import fetch_page, _get_cache_path


def run_test():
    print("=== Test 1: Fetching https://www.notion.so (Initial / Fresh) ===")
    url1 = "https://www.notion.so"
    is_cached_before_1 = _get_cache_path(url1).exists()
    start_t1 = time.perf_counter()
    content1 = fetch_page(url1)
    elapsed_t1 = time.perf_counter() - start_t1

    print(f"From Cache: {is_cached_before_1}")
    print(f"Elapsed Time: {elapsed_t1:.4f}s")
    print(f"Content Length: {len(content1)} characters")
    print(f"First 500 chars snippet:\n{'-'*40}\n{content1[:500]}\n{'-'*40}\n")

    print("=== Test 2: Fetching https://www.notion.so again (Cached Call) ===")
    is_cached_before_2 = _get_cache_path(url1).exists()
    start_t2 = time.perf_counter()
    content2 = fetch_page(url1)
    elapsed_t2 = time.perf_counter() - start_t2

    print(f"From Cache: {is_cached_before_2}")
    print(f"Elapsed Time: {elapsed_t2:.4f}s")
    print(f"Side-by-side comparison: Call 1 took {elapsed_t1:.4f}s vs Call 2 (Cache) took {elapsed_t2:.4f}s")
    assert content1 == content2, "Cached content does not match initial content!"
    print("Assertion passed: Cached content matches exactly.\n")

    print("=== Test 3: Fetching https://linear.app (Fresh / Different URL) ===")
    url2 = "https://linear.app"
    is_cached_before_3 = _get_cache_path(url2).exists()
    start_t3 = time.perf_counter()
    content3 = fetch_page(url2)
    elapsed_t3 = time.perf_counter() - start_t3

    print(f"From Cache: {is_cached_before_3}")
    print(f"Elapsed Time: {elapsed_t3:.4f}s")
    print(f"Content Length: {len(content3)} characters")
    print(f"First 500 chars snippet:\n{'-'*40}\n{content3[:500]}\n{'-'*40}\n")

    print("=== All tests completed successfully ===")


if __name__ == "__main__":
    run_test()
