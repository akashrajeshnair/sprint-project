from rag_service import service


if __name__ == "__main__":
    result = service.sync_uploads_incremental()
    processed = result.get("processed", [])
    skipped = result.get("skipped", [])
    failed = result.get("failed", [])

    print(f"Processed: {len(processed)} file(s)")
    print(f"Skipped (already indexed): {len(skipped)} file(s)")
    print(f"Failed: {len(failed)} file(s)")

    for item in processed:
        print(f"  - {item['file_name']}: {item['chunks']} chunks")

    for name in skipped:
        print(f"  - skipped: {name}")

    for item in failed:
        print(f"  - failed: {item['file_name']} ({item['error']})")
