import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    print("--- 接続されているオーディオ機器一覧 ---")
    found_mic = False
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            dev_name = p.get_device_info_by_host_api_device_index(0, i).get('name')
            channels = p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')
            rate = p.get_device_info_by_host_api_device_index(0, i).get('defaultSampleRate')
            print(f"デバイスID: {i} | 名前: {dev_name}")
            print(f"  └ 最大入力チャンネル数: {channels}")
            print(f"  └ サンプルレート: {rate}")
            print("------------------------------------------------")
            found_mic = True

    if not found_mic:
        print("【警告】マイク入力が見つかりませんでした。マイクは接続されていますか？")
    
    p.terminate()

if __name__ == "__main__":
    list_audio_devices()