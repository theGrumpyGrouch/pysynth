project('audio_playback', 'c')


deps = [
]

shared_library(
  'libplayback', 'playback.c', 
  link_args : ['-lminiaudio', '-dl', '-lpthread', '-lm'], 
  dependencies : deps,
)
