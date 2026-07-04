# Storage

Prometheus and Loki use PVCs in kind/local profiles. Grafana persistence is enabled only for the production reference profile, with one replica and SQLite.

`make uninstall` preserves PVCs. `make purge CONFIRM_PURGE=yes` removes release resources and PVC data.
