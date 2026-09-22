# SELinux bring-up

No permissive policy is shipped. Do not add broad access to the generic `system_app` domain. Bring up the base APK first, collect real AVCs, then add a dedicated MiuiCit domain and dedicated factory-service domains only as required. Reuse the existing mondrian labels for display, fingerprint, battery, torch and sensor objects.
