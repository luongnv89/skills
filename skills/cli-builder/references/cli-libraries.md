# CLI Libraries by Language

Recommended libraries, rationale, and starter scaffolds for building CLI tools.

## Selection Guide

| Language | Recommended | Why | Alternatives |
|----------|-------------|-----|-------------|
| Python | click | Decorators, composable, great docs | argparse (stdlib), typer |
| JavaScript/TS | commander | Lightweight, intuitive API | yargs, oclif |
| Go | cobra | Industry standard, completions built-in | kong, urfave/cli |
| Rust | clap | Derive macros, excellent error messages | argh |
| Java/Kotlin | picocli | Annotations, GraalVM native support | commons-cli |
| Ruby | thor | Rails-style generators, clean DSL | optparse (stdlib) |

---

## Python

### click (recommended)

**Why**: Decorator-based, composable command groups, automatic help generation, type validation, testing support via `CliRunner`.

```bash
pip install click
```

**Starter scaffold**:

```python
# cli.py
import click

@click.group()
@click.version_option()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def cli(ctx, verbose):
    """My CLI tool — does useful things."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

@cli.command()
@click.argument("name")
@click.option("--greeting", "-g", default="Hello", help="Greeting to use.")
def greet(name, greeting):
    """Greet someone by name."""
    click.echo(f"{greeting}, {name}!")

if __name__ == "__main__":
    cli()
```

**Entry point** (`pyproject.toml`):
```toml
[project.scripts]
mytool = "mytool.cli:cli"
```

### argparse (stdlib)

**Why**: No dependencies, part of Python standard library, good for simple CLIs.

```python
# cli.py
import argparse
import sys

def create_parser():
    parser = argparse.ArgumentParser(description="My CLI tool — does useful things.")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output.")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    greet_parser = subparsers.add_parser("greet", help="Greet someone by name.")
    greet_parser.add_argument("name", help="Name to greet.")
    greet_parser.add_argument("--greeting", "-g", default="Hello", help="Greeting to use.")

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "greet":
        print(f"{args.greeting}, {args.name}!")
    else:
        parser.print_help()
        sys.exit(2)

if __name__ == "__main__":
    main()
```

### typer

**Why**: Type-hint driven, auto-generates help from function signatures, built on click.

```bash
pip install typer
```

```python
# cli.py
import typer

app = typer.Typer(help="My CLI tool — does useful things.")

@app.command()
def greet(
    name: str = typer.Argument(..., help="Name to greet."),
    greeting: str = typer.Option("Hello", "--greeting", "-g", help="Greeting to use."),
):
    """Greet someone by name."""
    typer.echo(f"{greeting}, {name}!")

if __name__ == "__main__":
    app()
```

---

## JavaScript / TypeScript

### commander (recommended)

**Why**: Lightweight, intuitive fluent API, TypeScript support, 100M+ weekly downloads.

```bash
npm install commander
```

**Starter scaffold**:

```javascript
// src/cli.js
const { Command } = require("commander");
const { version } = require("../package.json");

const program = new Command();

program
  .name("mytool")
  .description("My CLI tool — does useful things.")
  .version(version);

program
  .command("greet <name>")
  .description("Greet someone by name.")
  .option("-g, --greeting <word>", "Greeting to use", "Hello")
  .action((name, options) => {
    console.log(`${options.greeting}, ${name}!`);
  });

program.parse();
```

**Entry point** (`package.json`):
```json
{
  "bin": {
    "mytool": "./src/cli.js"
  }
}
```

### yargs

**Why**: Rich feature set, middleware support, async commands.

```bash
npm install yargs
```

```javascript
// src/cli.js
const yargs = require("yargs/yargs");
const { hideBin } = require("yargs/helpers");

yargs(hideBin(process.argv))
  .scriptName("mytool")
  .command(
    "greet <name>",
    "Greet someone by name.",
    (yargs) => {
      yargs.positional("name", { describe: "Name to greet", type: "string" });
    },
    (argv) => {
      const greeting = argv.greeting || "Hello";
      console.log(`${greeting}, ${argv.name}!`);
    }
  )
  .option("greeting", { alias: "g", type: "string", default: "Hello", describe: "Greeting to use" })
  .help()
  .version()
  .parse();
```

### oclif

**Why**: Full framework for complex CLIs, plugin system, auto-generated docs.

```bash
npx oclif generate mytool
```

---

## Go

### cobra (recommended)

**Why**: Used by Docker, Kubernetes, Hugo. Built-in completions, persistent flags, auto help.

```bash
go get -u github.com/spf13/cobra@latest
```

**Starter scaffold**:

```go
// cmd/root.go
package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var verbose bool

var rootCmd = &cobra.Command{
	Use:   "mytool",
	Short: "My CLI tool — does useful things.",
	Long:  "A longer description of what mytool does.",
}

var greetCmd = &cobra.Command{
	Use:   "greet [name]",
	Short: "Greet someone by name.",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		greeting, _ := cmd.Flags().GetString("greeting")
		fmt.Printf("%s, %s!\n", greeting, args[0])
	},
}

func init() {
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose output")
	greetCmd.Flags().StringP("greeting", "g", "Hello", "Greeting to use")
	rootCmd.AddCommand(greetCmd)
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}
```

```go
// main.go
package main

import "mytool/cmd"

func main() {
	cmd.Execute()
}
```

### kong

**Why**: Struct-tag driven, zero code generation, excellent for simple CLIs.

```go
// main.go
package main

import (
	"fmt"

	"github.com/alecthomas/kong"
)

type CLI struct {
	Verbose bool      `short:"v" help:"Enable verbose output."`
	Greet   GreetCmd  `cmd:"" help:"Greet someone by name."`
}

type GreetCmd struct {
	Name     string `arg:"" help:"Name to greet."`
	Greeting string `short:"g" default:"Hello" help:"Greeting to use."`
}

func (g *GreetCmd) Run() error {
	fmt.Printf("%s, %s!\n", g.Greeting, g.Name)
	return nil
}

func main() {
	var cli CLI
	ctx := kong.Parse(&cli)
	ctx.FatalIfErrorf(ctx.Run())
}
```

---

## Rust

### clap (recommended)

**Why**: Derive macros, compile-time validation, excellent error messages, completions.

```toml
# Cargo.toml
[dependencies]
clap = { version = "4", features = ["derive"] }
```

**Starter scaffold**:

```rust
// src/main.rs
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "mytool", version, about = "My CLI tool — does useful things.")]
struct Cli {
    #[arg(short, long, global = true)]
    verbose: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Greet someone by name.
    Greet {
        /// Name to greet.
        name: String,

        /// Greeting to use.
        #[arg(short, long, default_value = "Hello")]
        greeting: String,
    },
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Greet { name, greeting } => {
            println!("{}, {}!", greeting, name);
        }
    }
}
```

---

## Java / Kotlin

### picocli (recommended)

**Why**: Annotation-driven, GraalVM native-image support, ANSI colors, completion scripts.

```xml
<!-- pom.xml -->
<dependency>
    <groupId>info.picocli</groupId>
    <artifactId>picocli</artifactId>
    <version>4.7.5</version>
</dependency>
```

**Starter scaffold**:

```java
// src/main/java/com/example/MyTool.java
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

@Command(name = "mytool", mixinStandardHelpOptions = true, version = "1.0.0",
         description = "My CLI tool — does useful things.")
public class MyTool implements Runnable {

    @Option(names = {"-v", "--verbose"}, description = "Enable verbose output.")
    boolean verbose;

    @Override
    public void run() {
        System.out.println("Use a subcommand. Try --help.");
    }

    @Command(name = "greet", description = "Greet someone by name.")
    void greet(
        @Parameters(paramLabel = "NAME", description = "Name to greet.") String name,
        @Option(names = {"-g", "--greeting"}, defaultValue = "Hello",
                description = "Greeting to use.") String greeting
    ) {
        System.out.printf("%s, %s!%n", greeting, name);
    }

    public static void main(String[] args) {
        int exitCode = new CommandLine(new MyTool()).execute(args);
        System.exit(exitCode);
    }
}
```

---

## Ruby

### thor (recommended)

**Why**: Clean DSL, used by Rails generators, built-in help and bash completion.

```bash
gem install thor
```

**Starter scaffold**:

```ruby
# lib/cli.rb
require "thor"

class MyCLI < Thor
  class_option :verbose, type: :boolean, aliases: "-v", desc: "Enable verbose output"

  desc "greet NAME", "Greet someone by name."
  option :greeting, type: :string, aliases: "-g", default: "Hello", desc: "Greeting to use"
  def greet(name)
    puts "#{options[:greeting]}, #{name}!"
  end
end

MyCLI.start(ARGV)
```

**Entry point** (`mytool.gemspec`):
```ruby
spec.executables = ["mytool"]
```

### optparse (stdlib)

**Why**: No dependencies, part of Ruby standard library.

```ruby
# lib/cli.rb
require "optparse"

options = { greeting: "Hello" }

parser = OptionParser.new do |opts|
  opts.banner = "Usage: mytool [command] [options]"

  opts.on("-g", "--greeting GREETING", "Greeting to use") do |g|
    options[:greeting] = g
  end

  opts.on("-v", "--verbose", "Enable verbose output") do
    options[:verbose] = true
  end
end

parser.parse!
command = ARGV.shift

case command
when "greet"
  name = ARGV.shift || abort("Error: NAME is required")
  puts "#{options[:greeting]}, #{name}!"
else
  puts parser.help
  exit 2
end
```
