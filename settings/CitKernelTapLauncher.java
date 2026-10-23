/*
 * Copyright (C) 2026 LF5
 *
 * SPDX-License-Identifier: Apache-2.0
 */

package com.android.settings.deviceinfo;

import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;
import android.util.Log;
import android.util.TypedValue;
import android.view.View;
import android.widget.ScrollView;
import android.widget.TextView;

import com.android.settings.R;

/**
 * MiuiCit entry points for AOSP/Lineage and MistOS Settings.
 *
 * MistOS: first kernel-version tap opens details; five taps inside the dialog launch CIT.
 * Other Settings implementations retain six taps on the kernel version preference.
 */
public final class CitKernelTapLauncher {

    private static final String TAG = "CitKernelTapLauncher";
    private static final String CIT_ACTION = "com.miui.cit.MAGIC_NUMBER";
    private static final String CIT_PACKAGE = "com.miui.cit";
    private static final String CIT_HOME_ACTIVITY = "com.miui.cit.home.HomeActivity";

    private static final int REQUIRED_TAPS = 6;
    private static final int REQUIRED_DIALOG_TAPS = 5;
    private static final long MAX_TAP_INTERVAL_MS = 3000L;

    private static int sTapCount;
    private static long sLastTapElapsedRealtime;

    private CitKernelTapLauncher() {}

    /**
     * The opening click is not counted. Only taps inside the details dialog count.
     * Closing the dialog discards the count instead of keeping hidden global state.
     */
    public static void showKernelDetails(Context context, String fullKernelVersion) {
        final TextView details = new TextView(context);
        details.setText(fullKernelVersion);
        details.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        final int padding = (int) (20 * context.getResources()
                .getDisplayMetrics().density + 0.5f);
        details.setPadding(padding, padding, padding, padding);
        details.setMinHeight(padding * 6);
        details.setClickable(true);

        final ScrollView content = new ScrollView(context);
        content.setFillViewport(true);
        content.addView(details);

        final AlertDialog dialog = new AlertDialog.Builder(context)
                .setTitle(R.string.kernel_version)
                .setView(content)
                .setPositiveButton(android.R.string.ok, null)
                .create();

        final int[] dialogTapCount = {0};
        final long[] lastDialogTap = {0L};

        final View.OnClickListener dialogTap = ignored -> {
            final long now = SystemClock.elapsedRealtime();
            if (lastDialogTap[0] == 0
                    || now - lastDialogTap[0] > MAX_TAP_INTERVAL_MS) {
                dialogTapCount[0] = 0;
            }
            lastDialogTap[0] = now;
            dialogTapCount[0]++;

            if (dialogTapCount[0] == REQUIRED_DIALOG_TAPS) {
                dialog.dismiss();
                launchCit(context);
            }
        };

        // Taps on the kernel text or empty dialog content count; scrolling does not.
        details.setOnClickListener(dialogTap);
        content.setOnClickListener(dialogTap);
        dialog.show();
    }

    /** Fallback for other ROMs: six clicks on the kernel-version preference. */
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
