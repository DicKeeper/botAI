import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ContentType
import asyncio
import openai
import os
from config import settings


bot = Bot(token=settings.bot_token)
dp = Dispatcher(bot)


async def convert_voice_to_text(voice_path):
    
    response = await openai.AsyncClient().whisper(
        file=open(voice_path, 'rb'),
        model="base"  
    )
    return response['text']

async def ask_openai_assistant(question):
    
    response = await openai.AsyncClient().create_assistant_session(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}]
    )
    return response['choices'][0]['message']['content']

async def text_to_speech(text):
    
    response = await openai.AsyncClient().text_to_speech(
        text=text,
        voice="voice_model"
    )
    
    audio_path = f'audio/{response["id"]}.ogg'
    with open(audio_path, 'wb') as f:
        f.write(response.audio)
    return audio_path


@dp.message_handler(content_types=ContentType.VOICE)
async def voice_handler(message: types.Message):
    
    voice = await message.voice.get_file()
    voice_path = f'voice/{voice.file_id}.oga'
    await voice.download(voice_path)

    
    text = await convert_voice_to_text(voice_path)

    
    answer = await ask_openai_assistant(text)

    
    audio_path = await text_to_speech(answer)

    
    with open(audio_path, 'rb') as audio:
        await message.reply_voice(voice=audio)

    os.remove(voice_path)
    os.remove(audio_path)

@dp.message_handler()
async def text_handler(message: types.Message):
    
    answer = await ask_openai_assistant(message.text)

    await message.reply(answer)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
