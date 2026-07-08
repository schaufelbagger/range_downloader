from pathlib import Path
import subprocess
import requests
import shutil
import argparse

from range_downloader.config import load_config

def download(
    url: str | None = None,
    filename: str | None = None,
    output_folder: str | None = None,
    ffmpeg_validate: bool | None = None,
):
    config = load_config()

    if url is not None:
        config.url = url
    if filename is not None:
        config.filename = filename
    if output_folder is not None:
        config.output_folder = output_folder
    if ffmpeg_validate is not None:
        config.ffmpeg_validate = ffmpeg_validate

    output_file = Path(config.output_folder) / config.filename
    urls = config.url
    if isinstance(urls, str):
        urls = [urls]



    for url in urls:
        next_bytes = 0
        chunk_cnt = 0
        url_cnt = 0
        raw = b''
        # download file stream in parts
        while True:
            headers = {"Range": f"bytes={str(next_bytes)}-"}
            response = requests.get(url, headers=headers, stream=True)
            cd = response.headers.get("Content-Disposition", "")

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
