---
name: system_health_monitor
description: Reports the host OS, CPU count, Python version, and disk usage.
category: system
capabilities: []
---

# System Health Monitor

Returns basic facts about the machine the agent is running on: operating system
and release, architecture, Python version, logical CPU count, and disk usage for
the root volume in gigabytes.

Read-only and instant, so it needs no approval.

## What it does not report

Despite "health" in the name, there is **no live CPU utilisation and no RAM
usage** — `cpu_count` is how many cores exist, not how busy they are. If the
user asks "what's using my CPU" or "how much memory is free", this skill cannot
answer it; say so rather than presenting core count as load.

Both flags default to true; set `include_disk` or `include_system_info` to false
only when the user wants one specific number.
