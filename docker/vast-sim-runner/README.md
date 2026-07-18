# Vast sim runner — build & smoke

## Build
```bash
docker build -t c4reqber/vast-sim-runner:latest docker/vast-sim-runner
```

## Local smoke (no Vast account)
```bash
echo '{"engine":"newton","type":"rigid_body","num_steps":30,"dt":0.0167}' > /tmp/c4_sim_config.json
docker run --rm -v /tmp/c4_sim_config.json:/tmp/c4_sim_config.json c4reqber/vast-sim-runner:latest
```

## Remote (VastAIDelegate)
Default `remote_argv` for engine `newton` is:
`python3 /app/vast_remote_runner.py --config /tmp/c4_sim_config.json`

Image name: `c4reqber/vast-sim-runner:latest` (push to your registry before renting).
