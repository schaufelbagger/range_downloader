import argparse
import os
from dataclasses import fields, MISSING
from pathlib import Path
from dataclasses import dataclass
import tomllib


@dataclass
class Config:
    url:str|list[str]
    filename:str = "out.mp4"
    output_folder:str = "."
    ffmpeg_validate:bool = False



def load_toml(path: Path = Path("config.toml")) -> dict:
    if not path.exists():
        return {}

    with open(path, mode="rb") as fp:
        config = tomllib.load(fp)
    return config


def load_dotenv(path: Path = Path(".env")) -> dict:
    env = {}
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip().strip("'\"")
    return env

def get_defaults(cls) -> dict[str, any]:
    """Extract default values and default-factory values from a dataclass."""
    defaults = {}
    for f in fields(cls):
        if f.default is not MISSING:
            defaults[f.name] = f.default
        elif f.default_factory is not MISSING:
            defaults[f.name] = f.default_factory()
        # else: no default – skip, it's required
    return defaults

def load_config() -> Config:
    # Get defaults from dataclass
    config_dict = get_defaults(Config)  # {'file_extension': '.mp4'}

    # Load TOML file (if exists)
    toml_data = load_toml(Path("config.toml"))
    config_dict.update(toml_data)

    # Load .env file (optional) and system environment
    env_vars = load_dotenv()  # from .env
    #env_vars.update(os.environ)  # system env overrides .env

    env_data = {}
    bool_fields = {f.name for f in fields(Config) if f.type == bool}
    for key, value in env_vars.items():
        config_key = key.lower().replace("-", "_")
        if key in bool_fields and isinstance(value, str):
            env_data[config_key] = value.lower() in ('true', '1', 'yes', 'on')
        else:
            env_data[config_key] = value
    config_dict.update(env_data)

    # CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", action='append', type=str, help="Use this specific URL")
    parser.add_argument("-e", "--filename", action='store', type=str, help="Output filename")
    parser.add_argument("-o", "--output-folder", action='store', type=str, help="Output folder")
    parser.add_argument("-f", "--ffmpeg-validate", action='store_const', const=True, default=None, help="Enable ffmpeg validation")
    args = parser.parse_args()
    # Convert dashes to underscores to match dataclass fields
    cli_data = {k.replace("-", "_"): v for k, v in vars(args).items() if v is not None}
    config_dict.update(cli_data)

    # Ensure required fields are present
    required = [f.name for f in fields(Config)
                if f.default == f.default_factory and f.default_factory is None]
    missing = [f for f in required if f not in config_dict or config_dict[f] is None]
    if missing:
        raise ValueError(f"Missing required config fields: {', '.join(missing)}")

    # Instantiate – dataclass will do basic type checking (but not coercion)
    return Config(**config_dict)