import pygame
import pygame._sdl2.audio as sdl2_audio

pygame.init()
# オーディオデバイスのリストを取得
devices = sdl2_audio.get_audio_device_names(False)
print("--- 利用可能なスピーカー ---")
for dev in devices:
    print(dev)
pygame.quit()