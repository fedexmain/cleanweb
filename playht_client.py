import os
import requests
from pyht import Client
from pyht.client import TTSOptions, Language
from datetime import datetime

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'static')
class PlayHTClient:
    def __init__(self, user_id, api_key, audio_dir=APP_STATIC):
        self.user_id = user_id
        self.api_key = api_key
        self.audio_dir = audio_dir
        self.client = Client(user_id=self.user_id, api_key=self.api_key)

        # Ensure the audio directory exists
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

        # Language map
        self.language_map = {
            "ENGLISH": Language.ENGLISH,
            "FRENCH": Language.FRENCH,
            "SPANISH": Language.SPANISH,
            "GERMAN": Language.GERMAN,
            "ARABIC": Language.ARABIC
        }

    def get_cloned_voices(self):
        """
        Fetch cloned voices from Play.ht.
        """
        url = "https://api.play.ht/api/v2/cloned-voices"
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for any HTTP errors
        return response.json()

    def get_prebuilt_voices(self):
        """
        Fetch prebuilt voices from Play.ht.
        """
        url = "https://api.play.ht/api/v2/voices"
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def text_to_speech(self, text, voice, language="ENGLISH", sample_rate=48000, quality="premium", speed=0.1, voice_guidance=1, style_guidance=10):
        """
        Convert text to speech and save it to the audio directory.
        """
        # Clean text input
        text = text.replace('.', '')

        # Select language
        selected_language = self.language_map.get(language.upper(), Language.ENGLISH)

        # Set TTS options
        options = TTSOptions(
            voice=voice,
            sample_rate=sample_rate,
            quality=quality,
            speed=speed,
            voice_guidance=voice_guidance,
            style_guidance=style_guidance
        )

        # Set voice engine
        voice_engine = "Play3.0-mini-http"

        # Generate the speech in chunks
        audio_chunks = []
        for chunk in self.client.tts(text, options, voice_engine):
            audio_chunks.append(chunk)

        # Save the audio to a file
        # Format the current time to use only valid characters for filenames
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')  # Format as YYYYMMDDHHMMSS
        audio_filename = f'tts_output/output_{timestamp}.mp3'
        audio_file = os.path.join(self.audio_dir, audio_filename)
        with open(audio_file, 'wb') as f:
            for chunk in audio_chunks:
                f.write(chunk)

        print(f"Audio generated and saved to: {audio_file}")
        return audio_filename

    def list_all_voices(self):
        """
        List all available voices (both prebuilt and cloned).
        Extracts the necessary details from the response JSON.
        """
        all_voices = []

        # Get cloned voices
        cloned_voices_response = self.get_cloned_voices()
        for voice in cloned_voices_response:
            all_voices.append({
                'id': voice['id'],
                'name': voice['name'],
                'accent': voice.get('accent'),
                'gender': voice.get('gender'),
                'language': voice.get('language'),
                'voice_engine': voice.get('voice_engine'),
                'is_cloned': voice.get('is_cloned', False),
                'sample': voice.get('sample')
            })

        # Get prebuilt voices
        prebuilt_voices_response = self.get_prebuilt_voices()
        for voice in prebuilt_voices_response:
            all_voices.append({
                'id': voice['id'],
                'name': voice['name'],
                'accent': voice.get('accent'),
                'gender': voice.get('gender'),
                'language': voice.get('language'),
                'voice_engine': voice.get('voice_engine'),
                'is_cloned': voice.get('is_cloned', False),
                'sample': voice.get('sample')
            })

        return all_voices

    def _get_headers(self):
        """
        Helper function to get the authorization headers.
        """
        return {
            "AUTHORIZATION": self.api_key,
            "X-USER-ID": self.user_id
        }

def main():
    # Initialize PlayHTClient with your Play.ht credentials
    client = PlayHTClient(
        user_id='001v9gL6rWOZ9lmnbSppLTr2HUE3',
        api_key='bbf066d8e8b843ad9cea0e912219cb29'
    )

    # Check available cloned voices
    #cloned_voices = client.get_cloned_voices()
    #print("Cloned Voices:", cloned_voices)

    # Check available prebuilt voices
    #prebuilt_voices = client.get_prebuilt_voices()
    #print("Prebuilt Voices:", prebuilt_voices)
    text=str(input('Enter what to say: '))
    voices = client.list_all_voices()
    voice_index = 0
    # Print details for each voice
    count=0
    for voice in voices:
        count+=1
        print(f"No{count}. Voice ID: {voice['id']}, Name: {voice['name']}, Language: {voice['language']}, Gender: {voice['gender']}, Accent: {voice['accent']}, Cloned: {voice['is_cloned']}, Sample: {voice['sample']}")
        print()
    voice_index=int(input(f'Choose with number: e.g 1,...{len(voices)}: '))-1
    selected_voice = voices[voice_index]

    print(f'\n selected_voice: {selected_voice["name"]}\n')
    input('Press enter to continue')
    # Generate text to speech
    output_file = client.text_to_speech(
        text=text, 
        voice=selected_voice['id'],  # Replace with a valid voice ID
        language="ENGLISH"
    )
    print(f"Audio generated: {output_file}")

    import pygame
    # Initialize pygame mixer
    pygame.mixer.init()


    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()

    # Keep the script running until the audio finishes
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


# Example usage
if __name__ == '__main__':
    main()
