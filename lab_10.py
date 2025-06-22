import os
import requests
import webbrowser
import pyttsx3
import json
import wikipedia
from vosk import Model, KaldiRecognizer
import pyaudio

wikipedia.set_lang("ru")  
MODEL_PATH = "vosk-model-small-ru-0.22"  
DOG_API_URL = "https://dog.ceo/api/breeds/image/random"


class DogAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)

        if not os.path.exists(MODEL_PATH):
            self.speak("Модель распознавания речи не найдена. Пожалуйста, скачайте её.")
            self.download_vosk_model()

        self.model = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192
        )

        self.current_image_url = ""
        self.current_image_data = None

    def download_vosk_model(self):
        """загружает модель Vosk, если её нет"""
        import zipfile
        print("Загрузка модели Vosk...")
        url = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
        try:
            r = requests.get(url, stream=True)
            with open("model.zip", "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            with zipfile.ZipFile("model.zip", "r") as zip_ref:
                zip_ref.extractall()
            os.remove("model.zip")
            print("Модель успешно загружена.")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            exit(1)

    def speak(self, text):
        """озвучивает текст"""
        print(f"Ассистент: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """слушает и распознаёт команду"""
        print("Слушаю...")
        while True:
            data = self.stream.read(4096, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                command = result.get("text", "").strip().lower()
                if command:
                    return command

    def fetch_random_dog(self):
        """загружает случайное изображение собаки"""
        try:
            response = requests.get(DOG_API_URL)
            if response.status_code == 200:
                data = response.json()
                self.current_image_url = data["message"]
                img_response = requests.get(self.current_image_url, stream=True)
                self.current_image_data = img_response.content
                return True
            else:
                self.speak("Не удалось получить изображение собаки.")
                return False
        except Exception as e:
            self.speak("Ошибка при загрузке изображения.")
            print(f"Ошибка: {e}")
            return False

    def show_image(self):
        """открывает изображение в браузере"""
        if self.current_image_url:
            webbrowser.open(self.current_image_url)
            self.speak("Вот изображение собаки.")
        else:
            self.speak("Сначала загрузите изображение командой 'следующая'.")

    def save_image(self):
        """сохраняет изображение на диск"""
        if self.current_image_data:
            try:
                breed = self.current_image_url.split("/")[-2]
                filename = f"dog_{breed}.jpg"
                with open(filename, "wb") as f:
                    f.write(self.current_image_data)
                self.speak(f"Изображение сохранено как {filename}.")
            except Exception as e:
                self.speak("Не удалось сохранить изображение.")
                print(f"Ошибка: {e}")
        else:
            self.speak("Нет изображения для сохранения.")

    def get_breed(self):
        """определяет породу собаки"""
        if self.current_image_url:
            breed = self.current_image_url.split("/")[-2]
            self.speak(f"Порода собаки: {breed}.")
        else:
            self.speak("Сначала загрузите изображение.")

    def get_breed_info(self):
        """ищет информацию о породе в Wikipedia"""
        if self.current_image_url:
            breed = self.current_image_url.split("/")[-2]
            try:
                summary = wikipedia.summary(breed, sentences=2)
                self.speak(f"Вот что я нашёл о породе {breed}: {summary}")
            except wikipedia.exceptions.PageError:
                self.speak(f"Не удалось найти информацию о породе {breed}.")
            except Exception as e:
                self.speak("Произошла ошибка при поиске информации.")
                print(f"Ошибка: {e}")
        else:
            self.speak("Сначала загрузите изображение.")

    def handle_command(self, command):
        """обрабатывает команды"""
        if "следующая" in command:
            if self.fetch_random_dog():
                self.speak("Загружено новое изображение собаки.")
        elif "показать" in command:
            self.show_image()
        elif "сохранить" in command:
            self.save_image()
        elif "назови породу" in command:
            self.get_breed()
        elif "расскажи о породе" in command:
            self.get_breed_info()
        else:
            self.speak("Я не понял команду. Попробуйте ещё раз.")

    def run(self):
        """основной цикл работы ассистента"""
        self.speak("Привет! Я голосовой ассистент, который покажет фотографии собак и расскажет о породе. Скажите 'следующая', чтобы начать.")
        while True:
            try:
                command = self.listen()
                print(f"Вы сказали: {command}")
                self.handle_command(command)
            except KeyboardInterrupt:
                self.speak("До свидания!")
                self.stream.stop_stream()
                self.stream.close()
                self.mic.terminate()
                break


if __name__ == "__main__":
    assistant = DogAssistant()
    assistant.run()
