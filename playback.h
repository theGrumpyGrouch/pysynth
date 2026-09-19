#pragma once

#include "miniaudio/miniaudio.h"
#include <math.h>

typedef void* audio_device_handle;

void data_callback(ma_device *pDevice, void *pOutput, const void *pInput, ma_uint32 frameCount);

audio_device_handle init_engine();
void cleanup_engine(audio_device_handle handle); 
void start_note(audio_device_handle handle, int index);
void stop_note(audio_device_handle handle, int index);
void set_wave(audio_device_handle handle, int type);

/*
 * Converts nth note on piano scale to frequency
 */
float noteToFreq(float n) { return pow(2, (n - 49) / 12) * 440; }
/*
 * Converts frequency to nth note on piano
 */
float freqToNote(float f) { return 49 + (12 * log2(f / 440)); }

// Helper function to convert amplitude to dB
float amptodb(float amp) {
    return 20.0f * log10f(fabsf(amp) + 1e-10f);  // Add small value to avoid log(0)
}

// Helper function to convert dB to amplitude
float dbtoamp(float db) {
    return powf(10.0f, db / 20.0f);
}
