#define MA_NO_DECODING
#define MA_NO_ENCODING

#include "playback.h"
#include "miniaudio/miniaudio.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DEVICE_FORMAT ma_format_f32
#define DEVICE_CHANNELS 1
#define DEVICE_SAMPLE_RATE 44100
#define RELEASE_TIME 0.1f
#define ATTACK_TIME 0.001f

typedef struct oscillator {
  float phase;
  float freq;
  float val;
  float amp;
  float filtered_val;
  ma_bool8 active;
  ma_bool8 released;
} osc_t;

void filter_wave(osc_t *osc, float cuttoff) {
  float smoothing_factor =
      (1.0f / DEVICE_SAMPLE_RATE) /
      ((1.0f / (2.0f * M_PI * cuttoff)) + (1.0f / DEVICE_SAMPLE_RATE));
  osc->filtered_val = osc->val * smoothing_factor +
                      osc->filtered_val * (1.0f - smoothing_factor);
}

void gen_wave(osc_t *osc, int type) {
  if (osc->active == MA_FALSE) {
    osc->val = 0.0f;
    osc->phase = 0.0f;
    return;
  }

  int k = 0;
  osc->val = 0.0f;
  switch (type) {
  case 1: // Sine
    osc->val = sinf(2.0f * (float)M_PI * osc->phase);
    break;
  case 2: // Square
    osc->val = osc->phase < 0.5f ? 1.0f : -1.0f;
    break;
  case 3: // Triangle
    if (osc->phase < 0.25f) {
      osc->val = 4.0f * osc->phase;
    } else if (osc->phase < 0.75f) {
      osc->val = 2.0f - 4.0f * osc->phase;
    } else {
      osc->val = -4.0f + 4.0f * osc->phase;
    }
    break;
  case 4: // Sawtooth
    osc->val = 2 * osc->phase - 1.0f;
    break;
  }
  osc->phase += osc->freq / DEVICE_SAMPLE_RATE;

  if (osc->phase > 1.0f) { // Prevents overflow after ~4hrs of playback
    osc->phase -= 1.0f;
  }
}

int number_active(osc_t osc[], int len) {
  int count = 0;
  for (int i = 0; i < len; ++i) {
    count += osc[i].active ? 1 : 0;
  }
  return count;
}

typedef struct audio_context {
  osc_t voices[88];
  ma_device device;
  volatile int wavetype;
} audio_t;

audio_device_handle init_engine() {
  audio_t *ctx;
  ctx = (audio_t *)malloc(sizeof(audio_t));
  ma_device_config deviceConfig;
  // ma_device device;
  if (!ctx)
    return NULL;

  for (int i = 0; i < 88; ++i) {
    ctx->voices[i].active = MA_FALSE;
    ctx->voices[i].freq = noteToFreq(i);
    ctx->voices[i].phase = 0;
    ctx->voices[i].val = 0;
    ctx->voices[i].amp = 0;
    ctx->voices[i].filtered_val = 0;
  }

  deviceConfig = ma_device_config_init(ma_device_type_playback);
  deviceConfig.playback.format = DEVICE_FORMAT;
  deviceConfig.playback.channels = DEVICE_CHANNELS;
  deviceConfig.sampleRate = DEVICE_SAMPLE_RATE;
  deviceConfig.dataCallback = data_callback;
  deviceConfig.pUserData = ctx;

  if (ma_device_init(NULL, &deviceConfig, &ctx->device) != MA_SUCCESS) {
    printf("Failed to open playback device.\n");
    free(ctx);
    return NULL;
  }
  printf("Device Name: %s\n", ctx->device.playback.name);

  if (ma_device_start(&ctx->device) != MA_SUCCESS) {
    printf("Failed to start playback device. \n");
    ma_device_uninit(&ctx->device);
    free(ctx);
    return NULL;
  }

  return (audio_device_handle)ctx;
}

void cleanup_engine(audio_device_handle handle) {
  if (!handle)
    return;
  audio_t *ctx = (audio_t *)handle;

  // Device Handling
  ma_device_stop(&ctx->device);
  ma_device_uninit(&ctx->device);

  free(ctx);
  return;
}

void start_note(audio_device_handle handle, int index) {
  if (!handle)
    return;
  audio_t *ctx = (audio_t *)handle;
  ctx->voices[index].active = MA_TRUE;
  ctx->voices[index].released = MA_FALSE;
  ctx->voices[index].amp = 0.0f;
}

void stop_note(void *handle, int index) {
  if (!handle)
    return;
  audio_t *ctx = (audio_t *)handle;
  // ctx->voices[index].active = MA_FALSE;
  ctx->voices[index].released = MA_TRUE;
}

void set_wave(audio_device_handle handle, int type) {
  if (!handle)
    return;
  audio_t *ctx = (audio_t *)handle;
  ctx->wavetype = type;
}

float attack_inc = 1.0f / (ATTACK_TIME * DEVICE_SAMPLE_RATE);
float release_dec = 1.0f / (RELEASE_TIME * DEVICE_SAMPLE_RATE);

void data_callback(ma_device *pDevice, void *pOutput, const void *pInput,
                   ma_uint32 frameCount) {
  // pUserData holds audio context
  audio_t *ctx = (audio_t *)pDevice->pUserData;
  float *out = (float *)pOutput;

  if (!ctx)
    return;

  // Clear sound & preemptive stop on silence
  memset(out, 0, frameCount * DEVICE_CHANNELS * sizeof(float));
  // int num_keys = number_active(ctx->voices, 88);

  // if (num_keys <= 0)
  //   return;

  float voices = 0;
  for (int i = 0; i < frameCount; ++i) {
    voices = 0;
    // Gen and Mix all voices
    for (int j = 0; j < 88; ++j) {

      if (ctx->voices[j].released) {
        ctx->voices[j].amp -= release_dec;
        if (ctx->voices[j].amp < 0.0f) {
          ctx->voices[j].amp = 0.0f;
          ctx->voices[j].released = MA_FALSE; 
          ctx->voices[j].active = MA_FALSE;
        }
      } else {
        if (ctx->voices[j].amp < 1.0f) {
          ctx->voices[j].amp += attack_inc;
          if (ctx->voices[j].amp > 1.0f ) ctx->voices[j].amp = 1.0f ;
        }
      }

      if (ctx->voices[j].active) {
        gen_wave(&ctx->voices[j], ctx->wavetype);
        filter_wave(&ctx->voices[j], 10000.0f);
        voices += ctx->voices[j].filtered_val * ctx->voices[j].amp;
      }
    }

    voices /= 8.0f;

    // Write to all channels (Stereo, Mono, etc)
    for (ma_uint32 c = 0; c < DEVICE_CHANNELS; c++) {
      out[i * DEVICE_CHANNELS + c] = voices;
    }
  }
}
