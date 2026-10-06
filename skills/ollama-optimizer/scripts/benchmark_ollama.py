#!/usr/bin/env python3
"""
Benchmark Ollama performance with the current configuration.
Measures tokens/second, time to first token, and memory usage.

Exit codes: 0 = JSON results on stdout; 1 = error, JSON {"error": ...} on stderr;
2 = invalid arguments (argparse usage message on stderr).
"""

import shutil
import subprocess
import time
import json
import sys
import re
from datetime import datetime


def run_command(cmd, timeout=120):
    """Run command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str)
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Timeout", -1
    except Exception as e:
        return None, str(e), -1


def get_ollama_models():
    """Get list of installed Ollama models."""
    stdout, _, code = run_command(["ollama", "list"])
    if code != 0 or not stdout:
        return []

    models = []
    for line in stdout.strip().split('\n')[1:]:  # Skip header
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def benchmark_model(model_name, prompt="Explain quantum computing in 100 words.", num_runs=3):
    """Benchmark a specific model."""
    results = {
        "model": model_name,
        "prompt": prompt,
        "runs": [],
        "timestamp": datetime.now().isoformat()
    }

    for i in range(num_runs):
        print(f"  Run {i+1}/{num_runs}...", file=sys.stderr)

        start_time = time.time()

        # Run ollama with verbose output to get timing
        stdout, stderr, code = run_command(
            ["ollama", "run", model_name, prompt, "--verbose"],
            timeout=300
        )

        end_time = time.time()
        total_time = end_time - start_time

        run_result = {
            "run_number": i + 1,
            "total_time_seconds": round(total_time, 2),
            "success": code == 0
        }

        if stderr:
            # Parse verbose output for metrics
            # Example: "total duration: 5.123456789s"
            duration_match = re.search(r"total duration:\s+([\d.]+)([a-z]+)", stderr)
            if duration_match:
                val, unit = duration_match.groups()
                if unit == "ms":
                    run_result["ollama_total_duration_ms"] = float(val)
                elif unit == "s":
                    run_result["ollama_total_duration_ms"] = float(val) * 1000

            # "load duration: 1.234s"
            load_match = re.search(r"load duration:\s+([\d.]+)([a-z]+)", stderr)
            if load_match:
                val, unit = load_match.groups()
                if unit == "ms":
                    run_result["load_duration_ms"] = float(val)
                elif unit == "s":
                    run_result["load_duration_ms"] = float(val) * 1000

            # "eval count: 123 tokens"
            eval_count_match = re.search(r"eval count:\s+(\d+)", stderr)
            if eval_count_match:
                run_result["eval_tokens"] = int(eval_count_match.group(1))

            # "eval duration: 2.345s"
            eval_duration_match = re.search(r"eval duration:\s+([\d.]+)([a-z]+)", stderr)
            if eval_duration_match:
                val, unit = eval_duration_match.groups()
                if unit == "ms":
                    run_result["eval_duration_ms"] = float(val)
                elif unit == "s":
                    run_result["eval_duration_ms"] = float(val) * 1000

            # "eval rate: 45.67 tokens/s"
            rate_match = re.search(r"eval rate:\s+([\d.]+)\s+tokens/s", stderr)
            if rate_match:
                run_result["tokens_per_second"] = float(rate_match.group(1))

            # "prompt eval count: 12 tokens"
            prompt_count_match = re.search(r"prompt eval count:\s+(\d+)", stderr)
            if prompt_count_match:
                run_result["prompt_tokens"] = int(prompt_count_match.group(1))

            # "prompt eval duration: 0.5s"
            prompt_duration_match = re.search(r"prompt eval duration:\s+([\d.]+)([a-z]+)", stderr)
            if prompt_duration_match:
                val, unit = prompt_duration_match.groups()
                if unit == "ms":
                    run_result["time_to_first_token_ms"] = float(val)
                elif unit == "s":
                    run_result["time_to_first_token_ms"] = float(val) * 1000

        if stdout:
            run_result["response_length"] = len(stdout)

        results["runs"].append(run_result)

    # Calculate averages
    successful_runs = [r for r in results["runs"] if r.get("success")]
    if successful_runs:
        avg = {}
        for key in ["tokens_per_second", "time_to_first_token_ms", "eval_duration_ms", "total_time_seconds"]:
            values = [r[key] for r in successful_runs if key in r]
            if values:
                avg[f"avg_{key}"] = round(sum(values) / len(values), 2)
        results["averages"] = avg

    return results


def check_gpu_memory():
    """Check current GPU memory usage."""
    # NVIDIA
    stdout, _, code = run_command(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"])
    if code == 0 and stdout:
        parts = stdout.strip().split(',')
        if len(parts) == 2 and all(p.strip().isdigit() for p in parts):
            return {
                "type": "nvidia",
                "used_mb": int(parts[0].strip()),
                "total_mb": int(parts[1].strip())
            }

    # macOS (approximate via vm_stat for unified memory)
    stdout, _, code = run_command(["vm_stat"])
    if code == 0:
        return {"type": "unified_memory", "note": "Use Activity Monitor for detailed GPU memory on macOS"}

    return None


def fail(message):
    """Print a JSON error on stderr and exit 1."""
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


def main():
    """Run benchmarks."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Ollama models")
    parser.add_argument("--model", "-m", help="Specific model to benchmark (default: first available)")
    parser.add_argument("--prompt", "-p", default="Explain quantum computing in 100 words.",
                        help="Prompt to use for benchmarking")
    parser.add_argument("--runs", "-r", type=int, default=3, help="Number of runs per model")
    parser.add_argument("--all", "-a", action="store_true", help="Benchmark all installed models")

    args = parser.parse_args()
    if args.runs < 1:
        parser.error(f"--runs must be 1 or more, got {args.runs}")

    if shutil.which("ollama") is None:
        fail("'ollama' was not found on PATH. Install Ollama from https://ollama.com/download, then retry.")

    # Check Ollama is running
    stdout, stderr, code = run_command(["ollama", "ps"])
    if code != 0:
        detail = f" ({stderr.strip()})" if stderr and stderr.strip() else ""
        fail(f"Ollama check failed for 'ollama ps'{detail}. Start it with 'ollama serve' and retry.")

    models = get_ollama_models()
    if not models:
        print(
            json.dumps({"error": "No models returned by 'ollama list'. Install one with 'ollama pull <model>' and retry."}),
            file=sys.stderr,
        )
        sys.exit(1)

    if args.model:
        if args.model not in models:
            print(
                json.dumps({
                    "error": (
                        f"Requested model '{args.model}' was not found. Available: {models}. "
                        "Choose an available model or run 'ollama pull <model>', then retry."
                    )
                }),
                file=sys.stderr,
            )
            sys.exit(1)
        models_to_test = [args.model]
    elif args.all:
        models_to_test = models
    else:
        models_to_test = [models[0]]

    results = {
        "benchmark_date": datetime.now().isoformat(),
        "prompt": args.prompt,
        "runs_per_model": args.runs,
        "gpu_memory_before": check_gpu_memory(),
        "models": []
    }

    for model in models_to_test:
        print(f"Benchmarking {model}...", file=sys.stderr)
        model_result = benchmark_model(model, args.prompt, args.runs)
        if "averages" not in model_result:
            print(
                f"Warning: all {args.runs} run(s) of '{model}' failed; no averages recorded. "
                f"Try 'ollama run {model} --verbose' to see the error.",
                file=sys.stderr,
            )
        results["models"].append(model_result)

    results["gpu_memory_after"] = check_gpu_memory()

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        fail("Benchmark interrupted before results were printed. Re-run to get results.")
    except Exception as exc:
        fail(
            f"benchmark_ollama.py stopped: {type(exc).__name__}: {exc}. "
            "Check that 'ollama list' works, then re-run."
        )
