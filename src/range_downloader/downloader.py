from pathlib import Path
import subprocess
import requests
import shutil
import argparse
import hashlib
from urllib.parse import urlparse
import os

from range_downloader.config import load_config

def download(
    url: str | None = None,
    filename: str | None = None,
    output_folder: str | Path | None = None,
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

    if isinstance(config.output_folder, str):
        config.output_folder = Path(config.output_folder)

    if not config.output_folder.is_dir():
        raise ValueError(f"the given output folder {config.output_folder} cannot be found")

    urls = config.url
    if isinstance(urls, str):
        urls = [urls]

    url_cnt = 1
    for url in urls:
        if config.filename is None and config.filename != "":
            current_filename = generate_filename(url, url_cnt)
        else:
            if len(urls) <= 1:
                current_filename = config.filename
            else:
                current_filename = f"{config.filename}_{url_cnt}"
        output_file = Path(config.output_folder / current_filename)
        result = download_one(
            url=url,
            output_file=output_file,
            ffmpeg_validate=config.ffmpeg_validate,
        )
        url_cnt = url_cnt + 1



def download_one(url: str,
                 output_file: Path,
                 ffmpeg_validate: bool):

    next_bytes = 0
    chunk_cnt = 0

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

        raw = response.content

        with open(output_file, "ab") as f_out:
            f_out.write(raw)

        next_bytes = next_bytes + current_content_size
        chunk_cnt = chunk_cnt + 1

    if ffmpeg_validate:
        # ffmpeg -v error -i out.mp4 -f null - 2>&1
        validate_command = ["ffmpeg", "-v", "error", "-i", f"{output_file.resolve()}", "-f", "null", "-"]
        result = subprocess.run(validate_command, capture_output=True, text=True)
        if result.returncode != 0:
            print("FFmpeg errors:\n", result.stderr)

    return output_file

def generate_filename(url, index, max_filename_length = 50):
    base = urlparse(url).path

    if base[0] == "/":
        base = base[1:]

    if not base:
        base = f"file_{index}"

    # Sanitize
    base = base.replace(" ", "_")
    base = base.replace("/", "_")
    base = "".join(c for c in base if c.isalnum() or c in "._-")
    base = base.strip("._- ")  # remove leading and trailing dangerous chars
    if len(base) > max_filename_length:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        name, ext = os.path.splitext(base)
        base = f"{name[:30]}_{url_hash}{ext}"
    return base