# logtail

A command-line tool for tailing and filtering JSON log output.

## Installation

Requires Node.js 18 or later.

    npm install -g logtail-cli

## Usage

    logtail [options] [file]

Pipe a process into it:

    my-server | logtail --level warn

### Options

| Option | Description |
|---|---|
| `-f, --follow` | Keep reading as the file grows |
| `-l, --level <level>` | Minimum level to show: debug, info, warn, error (default: info) |
| `-g, --grep <pattern>` | Show only lines whose message matches the pattern |
| `--json` | Print matching lines as raw JSON |
| `--no-color` | Disable colored output |

## Configuration

logtail reads defaults from `~/.logtailrc` (JSON), for example `{"level": "warn", "color": false}`.

## Development

    git clone https://github.com/acme/logtail
    cd logtail
    npm install
    npm test

## License

MIT
