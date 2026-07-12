import subprocess

def safe_compress_file(source_path: str, archive_name: str, timeout: int = 10):
    """
    Compresses source_path into <archive_name>.tar.gz using the OS tar tool.

    Safety measures:
    - shell=False (default): arguments passed as a list, so the OS never
      runs a shell parser over them. Characters like ; | & $() are inert.
    - Caller is responsible for validating archive_name before this runs
      (see validate_export_filename) — defense in depth, not relied on alone.
    """
    output_path = f"exports/{archive_name}.tar.gz"
    result = subprocess.run(
        ["tar", "-czf", output_path, source_path],
        shell=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False
    )
    return result, output_path