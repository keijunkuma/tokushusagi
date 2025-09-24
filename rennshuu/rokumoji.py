import pyaudio

p = pyaudio.PyAudio()

print("Available audio devices:")
print("------------------------")

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"Device Index: {info['index']}")
    print(f"  Name: {info['name']}")
    print(f"  Max Input Channels: {info['maxInputChannels']}")
    print("------------------------")

p.terminate()