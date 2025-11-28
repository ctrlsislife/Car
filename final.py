import cv2
import time
import serial
import serial.tools.list_ports
import random
import threading

# FND 디스플레이에 숫자를 보내는 함수
def send_fnd(data):
    sendData = f"FND={data}\n"
    my_serial.write(sendData.encode())

# 졸음운전 감지 시 부저를 울리는 함수
def send_buzzer(freq):
    sendData = f"BUZZER={freq}\n"
    my_serial.write(sendData.encode())

# 시리얼 포트를 읽는 쓰레드 함수
def serial_read_thread():
    while True:
        if my_serial.in_waiting > 0:
            incoming_data = my_serial.readline().decode('utf-8').strip()
            print(f"수신된 데이터: {incoming_data}")

# 얼굴 및 눈 인식을 통해 졸음운전을 감지하는 함수
def main():
    camera = cv2.VideoCapture(0)
    camera.set(3, 640)
    camera.set(4, 480)
    

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    sleep_count = 0
    sleep_detected = False  # 졸음운전 상태를 추적하는 변수

    while camera.isOpened():
        _, image = camera.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100), flags=cv2.CASCADE_SCALE_IMAGE)

        if len(faces):
            for (x, y, w, h) in faces:
                cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)

                face_gray = gray[y:y + h, x:x + w]
                face_color = image[y:y + h, x:x + w]

                eyes = eye_cascade.detectMultiScale(face_gray, scaleFactor=1.2, minNeighbors=5)

                if len(eyes) == 0:
                    if not sleep_detected:  # 졸음운전이 처음 감지되었을 때
                        if sleep_count < 50:
                            sleep_count += 1
                        if sleep_count >= 50:
                            print("졸음운전 감지!")
                            send_buzzer(1000)  # 부저 울리기
                            send_fnd(random.randint(1, 2))  # FND에 랜덤 숫자 전송
                            sleep_detected = True  # 졸음운전 상태가 감지되었으므로 계속 부저 울리기
                else:
                    if sleep_detected:  # 졸음운전이 감지된 후 눈을 뜬 경우에도 부저 계속 울림
                        send_buzzer(1000)

                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(face_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
                
        print(sleep_count)
        cv2.imshow('result', image)

        if cv2.waitKey(10) == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if 'Arduino Uno' in p.description:
            print(f"{p} 포트에 연결하였습니다.")
            my_serial = serial.Serial(p.device, baudrate=9600, timeout=1.0)
            time.sleep(2.0)

    # 시리얼 포트를 읽는 쓰레드 시작
    t1 = threading.Thread(target=serial_read_thread)
    t1.daemon = True
    t1.start()

    # 메인 함수 실행
    main()

    my_serial.close()
