# logsnap

Turn thousands of noisy log lines into a one-screen summary: error clusters, first and last
occurrence, and the lines that changed since the last deploy.

```bash
pip install logsnap
logsnap app.log            # summary of one file
kubectl logs api | logsnap # works on stdin
```

- Groups similar lines by template (numbers, IDs and timestamps are masked)
- Shows what is new since a saved baseline (`logsnap --baseline prod.snap`)
- Runs locally; no data leaves your machine
- Single binary-free Python package, Python 3.9+

Website: https://logsnap.dev · Source: https://github.com/example/logsnap

Made by Alex Chen (@alexbuilds on X). MIT licensed.
