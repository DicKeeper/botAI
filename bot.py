import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ContentType
from aiogram.utils import executor
import openai
from config import settings
import asyncio
from openai import AsyncOpenAI


logging.basicConfig(level=logging.INFO)


bot = Bot(token=settings.telegram_token)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


client = AsyncOpenAI(
    api_key=settings.openai_api_key,
)

async def transcribe_voice(file_path):

    with open(file_path, 'rb') as audio_file:
        transcript = await client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1"
        )
    return transcript['text']

async def generate_response(question):
   
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ],
        model="gpt-3.5-turbo",
    )
    return chat_completion['choices'][0]['message']['content']

async def synthesize_speech(text):
  
    response = await client.audio.synthesize(
        input=text,
        voice="en_us_001",
        format="mp3"
    )
    return response['audio_content']

@dp.message_handler(content_types=ContentType.VOICE)
async def handle_voice_message(message: types.Message):
   
    file_info = await bot.get_file(message.voice.file_id)
    file_path = file_info.file_path
    await bot.download_file(file_path, 'voice_message.ogg')
    
   
    text = await transcribe_voice('voice_message.ogg')
    await message.reply(f"Transcribed text: {text}")
    
   
    answer = await generate_response(text)
    await message.reply(f"Answer: {answer}")
    
    
    audio_data = await synthesize_speech(answer)
    with open('response.mp3', 'wb') as audio_file:
        audio_file.write(audio_data)

   
    with open('response.mp3', 'rb') as audio_file:
        await message.reply_voice(audio_file)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
