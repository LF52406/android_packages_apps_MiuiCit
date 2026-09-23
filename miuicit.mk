# ROM-agnostic MiuiCit integration.

PRODUCT_PACKAGES += \
    MiuiCit \
    miuicit_mondrian_config \
    miuicit_hardware_init

# Xiaomi factory HAL/runtime is intentionally not auto-enabled.
# Import it for analysis with tools/import-stock-runtime.sh, then enable
# individual services only after their ELF dependencies and SELinux policy
# have been validated on the target build.
