# Range Downloader

A lightweight Python tool that downloads media files (e.g. MP4) using HTTP Range requests. 
It fetches a remote resource in chunks, reassembles them locally, and optionally validates the resulting file with `ffmpeg`.


## Installation

1. Clone the repository:
2. (Optional) Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```
3. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

```
python -m range_downloader
```
or directly
```
python __main__.py
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for improvements, bug fixes, or new features.