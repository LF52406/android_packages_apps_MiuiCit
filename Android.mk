LOCAL_PATH := $(call my-dir)

# Keep the base integration on legacy Make deliberately.
#
# PRODUCT_PACKAGES existence is validated by Kati. Defining these three core
# modules directly in Android.mk makes them visible to Kati without relying on
# Soong namespace export/discovery, which is more portable across AOSP-derived
# ROM trees.

include $(CLEAR_VARS)
LOCAL_MODULE := MiuiCit
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := prebuilt/MiuiCit.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := platform
LOCAL_PRODUCT_MODULE := true
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)

include $(CLEAR_VARS)
LOCAL_MODULE := miuicit_mondrian_config
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_CLASS := ETC
LOCAL_SRC_FILES := config/mondrian/cit_param_config.json
LOCAL_MODULE_STEM := cit_param_config.json
LOCAL_MODULE_PATH := $(TARGET_OUT_ODM_ETC)
include $(BUILD_PREBUILT)

include $(CLEAR_VARS)
LOCAL_MODULE := miuicit_hardware_init
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_CLASS := ETC
LOCAL_SRC_FILES := init/init.miuicit.rc
LOCAL_MODULE_STEM := init.miuicit.rc
LOCAL_MODULE_PATH := $(TARGET_OUT_VENDOR_ETC)/init
include $(BUILD_PREBUILT)
