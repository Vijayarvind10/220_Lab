# CSE 220 Lab 1 Workflow

## What I set up
- I used a Google Cloud n2-standard-4 VM to get an x86_64 Ubuntu host with Docker.
- I cloned the `cse220` branch of `Scarab-infra` on the VM.
- I edited `cse220/lab1.json` to include the four configs: `map2_width2`, `map2_width10`, `map10_width2`, `map10_width10`.
- I updated helper scripts: forced `--platform linux/amd64` and `-j1` builds; kept the simple `run.sh` arg parsing; added `plot_metrics.py` to plot all four metrics.

## How I ran the lab
- Built the Docker image and pulled SPEC traces: `./run.sh -o /home/ubuntu/cse220_home -b 2`.
- Launched all 92 trace-based simulations: `./run.sh -o /home/ubuntu/cse220_home -s 4 -e lab1`.
- Generated CSV stats for each run: `./run.sh -p 1 -o /home/ubuntu/cse220_home -e lab1`.
- Created grouped-bar plots for IPC, branch mispred, D-cache miss, and I-cache miss: `python3 cse220/plot/plot_metrics.py -o /home/ubuntu/plot/lab1 -d /home/ubuntu/cse220_home/lab1.json -s /home/ubuntu/cse220_home/exp/simulations`.

## Files in this repo
- `lab1.json` — the experiment descriptor (23 SPEC benchmarks, four configs).
- `plot_metrics.py` — the plotting script that reads the CSVs and draws all four figures with an average bar.
- `README.md` — these notes.
