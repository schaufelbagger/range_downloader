

from pathlib import Path
import subprocess
import requests
import shutil
import argparse

from range_downloader.config import load_config


def main():

    config = load_config()

    output_file = Path(config.output_folder) / config.filename
    urls = config.url
    if isinstance(urls, str):
        urls = [urls]

    next_bytes = 0
    chunk_cnt = 0
    url_cnt = 0
    raw = b''

    for url in urls:
        # download file stream in parts
        while True:
            headers = {"Range": f"bytes={str(next_bytes)}-"}
            response = requests.get(url, headers=headers, stream=True)

            if response.status_code == 416:  # Range not satisfiable
                print("Range not satisfiable")
                break
            if response.status_code != 206:  # Partial content
                raise ValueError(f"HTTP {response.status_code}\n{response.content}")

            current_content_size = int(response.headers["Content-Length"])
            if current_content_size <= 0:
                print("No content received - end of stream")
                break

            raw = raw + response.content

            next_bytes = next_bytes + current_content_size

            chunk_cnt = chunk_cnt + 1


        with open(output_file, "wb") as f_out:
            f_out.write(raw)

        url_cnt = url_cnt + 1

        if config.ffmpeg_validate:
            # ffmpeg -v error -i out.mp4 -f null - 2>&1
            validate_command = ["ffmpeg", "-v", "error", "-i", f"{output_file.resolve()}", "-f", "null", "-"]
            result = subprocess.run(validate_command, capture_output=True, text=True)
            if result.returncode != 0:
                print("FFmpeg errors:\n", result.stderr)


if __name__ == "__main__":
    main()