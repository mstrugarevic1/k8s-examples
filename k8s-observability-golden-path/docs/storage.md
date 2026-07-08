# Storage

VictoriaMetrics and Loki use PVCs in kind/local profiles. In production, `vmstorage` uses PVCs and Loki uses object storage. Grafana persistence is enabled only for the production reference profile, with one replica and SQLite.

`make uninstall` preserves PVCs. `make purge CONFIRM_PURGE=yes` removes release resources and PVC data.
