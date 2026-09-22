/*
 * Copyright (C) 2026 LF5
 *
 * SPDX-License-Identifier: Apache-2.0
 */

package com.android.settings.deviceinfo;

import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;
import android.util.Log;

/**
 * Launches Xiaomi CIT after five consecutive taps on the kernel version preference.
 *
 * This class deliberately has no compile-time dependency on MiuiCit. Settings remains buildable
 * even when MiuiCit is not present in a product; on the fifth tap the explicit activity launch
 * simply fails closed and is logged.
 */
public final class CitKernelTapLauncher {

    private static final String TAG = "CitKernelTapLauncher";

    private static final String CIT_ACTION = "com.miui.cit.MAGIC_NUMBER";
    private static final String CIT_PACKAGE = "com.miui.cit";
    private static final String CIT_HOME_ACTIVITY = "com.miui.cit.home.HomeActivity";

    private static final int REQUIRED_TAPS = 5;
    private static final long MAX_TAP_INTERVAL_MS = 3000L;

    private static int sTapCount;
    private static long sLastTapElapsedRealtime;

    private CitKernelTapLauncher() {}

    /**
     * Counts a kernel-version tap and opens CIT on the fifth consecutive tap.
     *
     * A pause longer than MAX_TAP_INTERVAL_MS resets the sequence. The method always consumes the
     * preference click so the kernel row behaves consistently on both classic and Catalyst Settings.
     */
    public static synchronized boolean onKernelVersionTap(Context context) {
        final long now = SystemClock.elapsedRealtime();

        if (sLastTapElapsedRealtime == 0
                || now - sLastTapElapsedRealtime > MAX_TAP_INTERVAL_MS) {
            sTapCount = 0;
        }

        sLastTapElapsedRealtime = now;
        sTapCount++;

        if (sTapCount < REQUIRED_TAPS) {
            return true;
        }

        sTapCount = 0;
        sLastTapElapsedRealtime = 0;

        final Intent intent = new Intent(CIT_ACTION)
                .setClassName(CIT_PACKAGE, CIT_HOME_ACTIVITY)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);

        try {
            context.startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException e) {
            Log.w(TAG, "MiuiCit is unavailable or cannot be launched", e);
        }

        return true;
    }
}
