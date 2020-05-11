import requests
import json
import re
import time
import threading
import pyttsx3
import speech_recognition as sr

API_KEY = 'tkHu_NhfVaDD'
PROJECT_TOKEN = 'tTMdT3m1oVWn'
RUN_TOKEN = 'tDc9UPLUVTU2'

class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            'api_key': self.api_key
        }
        self.data = self.get_data()

    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
        return json.loads(response.text)

    def get_total_cases(self):
        data = self.data['total']
        for content in data:
            if content['name'] == 'Coronavirus Cases:':
                return content['value']
    
    def get_total_deaths(self):
        data = self.data['total']
        for content in data:
            if content['name'] == 'Deaths:':
                return content['value']

    def get_total_recovered(self):
        data = self.data['total']
        for content in data:
            if content['name'] == 'Recovered:':
                return content['value']

    def get_country_data(self, country):
        data = self.data['country']
        for content in data:
            if content['name'].lower() == country.lower():
                return content
        return 'Country not found'

    def get_countries(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())
        return countries
    
    def update_api(self):
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

        def poll():
            time.sleep(0.1) # back to main thread
            old_data = self.data
            while(True):
                new_data = self.get_data()
                if(new_data != old_data):
                    self.data = new_data
                    print('Data updated')
                    break
                time.sleep(5)
        thread = threading.Thread(target=poll)
        thread.start()

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('Listening...')
        audio = r.listen(source)
        speech = ''
        try:
            speech = r.recognize_google(audio)
        except sr.RequestError:
            print('API unavailable')
        except sr.UnknownValueError:
            print('Unable to recognize speech')
            speech = ''
    return speech.lower()

def main():
    data = Data(API_KEY, PROJECT_TOKEN)
    EXIT_PHRASE = ['stop', 'exit']
    UPDATE_COMMAND = 'update'
    country_list = list(data.get_countries())

    TOTAL_PATTERNS= {
        re.compile('[\w\s]+ total [\w\s]+ cases'):data.get_total_cases,
        re.compile('[\w\s]+ total cases'):data.get_total_cases,
        re.compile('[\w\s]+ total [\w\s]+ deaths'):data.get_total_deaths,
        re.compile('[\w\s]+ total deaths'):data.get_total_deaths,
        re.compile('[\w\s]+ worldwide deaths'):data.get_total_deaths,
        re.compile('[\w\s]+ total [\w\s] + recovered'):data.get_total_recovered,
        re.compile('[\w\s]+ total recovered'):data.get_total_recovered
    }

    COUNTRY_PATTERNS= {
        re.compile('[\w\s]+ cases [\w\s]+'): lambda country: data.get_country_data(country)['total_cases'],
        re.compile('[\w\s]+ deaths [\w\s]+'): lambda country: data.get_country_data(country)['total_deaths'],
        re.compile('[\w\s]+ recovered [\w\s]+'): lambda country: data.get_country_data(country)['total_recovered']
    }

    while(True):
        speech = listen()
        print(speech)
        result = None

        for pattern, func in COUNTRY_PATTERNS.items():
            if pattern.match(speech):
                words = set(speech.split(' '))
                for country in country_list:
                    if country in words:
                        result = func(country)
                break

        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(speech):
                result = func()
                break
        
        if speech in EXIT_PHRASE:
            break # exit loop
        
        if speech == UPDATE_COMMAND:
            result = 'Data is being updated...'
            data.update_api()
        
        if result:
            print(result)
            speak(result)
        elif speech != '':
            print('I didn\'t understand that, try again')
            speak('I didn\'t understand that, try again')

if __name__ == '__main__':
    main()