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
import android.view.View;
import android.widget.TextView;

/**
 * MiuiCit integration. MistOS expands kernel details in the existing text view,
 * then launches CIT on five further taps; other ROMs use six preference taps.
 */
public final class CitKernelTapLauncher {
    private static final String TAG = "CitKernelTapLauncher";
    private static final String CIT_ACTION = "com.miui.cit.MAGIC_NUMBER";
    private static final String CIT_PACKAGE = "com.miui.cit";
    private static final String CIT_HOME_ACTIVITY = "com.miui.cit.home.HomeActivity";

    private static final int REQUIRED_TAPS = 6;
    private static final int REQUIRED_INLINE_TAPS = REQUIRED_TAPS - 1;
    private static final long MAX_TAP_INTERVAL_MS = 3000L;

    private static int sTapCount;
    private static long sLastTapElapsedRealtime;

    private CitKernelTapLauncher() {}

    /**
     * A fresh listener is installed per MistOS kernel TextView binding.
     * The first tap reveals the full kernel text inline (no dialog); five
     * additional rapid taps on the expanded text launch CIT.
     */
    public static void installMistKernelTapListener(TextView kernel, String fullKernelVersion) {
        kernel.setOnClickListener(new View.OnClickListener() {
            private boolean expanded;
            private int additionalTaps;
            private long lastTapElapsedRealtime;

            @Override
            public void onClick(View view) {
                final long now = SystemClock.elapsedRealtime();
                if (!expanded) {
                    kernel.setText(fullKernelVersion);
                    expanded = true;
                    additionalTaps = 0;
                    lastTapElapsedRealtime = now;
                    return;
                }

                if (lastTapElapsedRealtime == 0L
                        || now - lastTapElapsedRealtime > MAX_TAP_INTERVAL_MS) {
                    additionalTaps = 0;
                }
                lastTapElapsedRealtime = now;

                // Do not collapse the TextView while the user taps the details.
                if (++additionalTaps == REQUIRED_INLINE_TAPS) {
                    additionalTaps = 0;
                    lastTapElapsedRealtime = 0L;
                    launchCit(view.getContext());
                }
            }
        });
    }

    /** Fallback for non-MistOS Settings: six clicks on the preference. */
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
        launchCit(context);
        return true;
    }

    private static void launchCit(Context context) {
        final Intent intent = new Intent(CIT_ACTION)
                .setClassName(CIT_PACKAGE, CIT_HOME_ACTIVITY)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);

        try {
            context.startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException e) {
            Log.w(TAG, "MiuiCit is unavailable or cannot be launched", e);
        }
    }
}
