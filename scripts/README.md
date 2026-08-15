# Scripts

PowerShell entry points used to reproduce setup, launches, and benchmark runs will live here.

Current script:

```powershell
.\scripts\collect_environment.ps1
```

It performs read-only inspection and prints JSON to standard output. Saving a new snapshot should be an explicit action so existing environment records are never overwritten silently.

