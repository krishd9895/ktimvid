import telebot
import os
import requests
from moviepy.editor import VideoFileClip
from webserver import keep_alive

my_secret = os.environ['TOKEN']
bot = telebot.TeleBot(my_secret)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    # Check if the message contains a downloadable video link
    if text.startswith("http"):
        try:
            
            

            # Download the video from the link
            msg = bot.send_message(chat_id, "Downloading the video...")
            video_file = download_video(text)
            bot.delete_message(chat_id, msg.message_id)

            # Ask the user for the start and end times for trimming
            msg = bot.send_message(chat_id, "Enter the start and end times (in seconds) separated by a space:")
            bot.register_next_step_handler(msg, ask_start_time, video_file)
        except Exception as e:
            bot.send_message(chat_id, f"Error: {str(e)}")
    else:
        bot.send_message(chat_id, "Please send a valid video link.")

def is_video_url(url):
    # Check if the URL points to a video file (you can add more video file extensions if needed)
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    return any(url.lower().endswith(ext) for ext in video_extensions)

def download_video(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open("video.mp4", "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
    return "video.mp4"

def ask_start_time(message, video_file):
    chat_id = message.chat.id
    text = message.text

    try:
        start_time, end_time = map(float, text.split())

        # Check if the duration of the trimmed video exceeds 60 seconds
        if end_time - start_time > 60:
            bot.send_message(chat_id, "The duration of the trimmed video cannot exceed 60 seconds. Please enter a valid duration.")
            msg = bot.send_message(chat_id, "Enter the start and end times (in seconds) separated by a space:")
            bot.register_next_step_handler(msg, ask_start_time, video_file)
            return

        # Trim the video
        msg = bot.send_message(chat_id, "Trimming the video...")
        bot.delete_message(chat_id, message.message_id)

        trimmed_video = trim_video(video_file, start_time, end_time)

        # Upload the trimmed video to Telegram
        msg = bot.send_message(chat_id, "Uploading the trimmed video...")
        with open(trimmed_video, 'rb') as trimmed_video_file:
            bot.send_video(chat_id, trimmed_video_file)

        # Clean up the files
        os.remove(video_file)
        os.remove(trimmed_video)
        bot.delete_message(chat_id, msg.message_id)
        bot.send_message(chat_id, "Process completed successfully.")
    except ValueError:
        bot.send_message(chat_id, "Invalid input. Please enter valid start and end times separated by space.")
    except Exception as e:
        bot.send_message(chat_id, f"Error: {str(e)}")

def trim_video(video_file, start_time, end_time):
    clip = VideoFileClip(video_file)
    trimmed_clip = clip.subclip(start_time, end_time)
    trimmed_clip_file = "trimmed_video.mp4"
    trimmed_clip.write_videofile(trimmed_clip_file, codec="libx264")
    return trimmed_clip_file

keep_alive()
bot.polling()
