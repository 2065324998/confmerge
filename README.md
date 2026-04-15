# confmerge

Hierarchical configuration merging for Python applications.

## Features

- Deep merge nested configuration dicts from multiple sources
- Configurable list merge strategies: extend, replace, unique
- Automatic type coercion for environment variables
- Variable interpolation with `${dotted.key}` syntax
- Schema validation

## Installation

```bash
pip install confmerge
```

## Quick Start

```python
from confmerge import load_config

config = load_config(
    defaults={"database": {"host": "localhost", "port": 5432}},
    config_path="config.yaml",
    env_prefix="MYAPP",
)
```

## License

MIT
