import tokenlol    # is my .py file where I stored my keys
import tweepy      # if you want you can store the keys locally I have added the code snippet down there
import openai
import requests
import io
# import os
import logging


# Set up authentication for Twitter API
auth = tweepy.OAuthHandler(tokenlol.api_key, tokenlol.api_secret)
auth.set_access_token(tokenlol.access_token, tokenlol.access_secret_token)
api = tweepy.API(auth)
openai.api_key = tokenlol.api_secret_openai


# Set up authentication for Twitter API locally
# auth = tweepy.OAuthHandler(os.environ['TWITTER_API_KEY'], os.environ['TWITTER_API_SECRET'])
# auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN'], os.environ['TWITTER_ACCESS_SECRET_TOKEN'])
# api = tweepy.API(auth)

# Set up authentication for OpenAI API
# openai.api_key = os.environ['OPENAI_API_SECRET']


# Define function to generate image with DALL-E
def generate_image(prompt: str) -> bytes or None:
    """Generates an image using the DALL-E OpenAI API, given a prompt string.

        Args:
            prompt (str): The prompt string to use for generating the image.

        Returns:
            bytes or None: The bytes of the generated image, or None if an error occurred.

        """
    try:
        response = openai.Completion.create(
            engine="image-alpha-001",
            prompt=prompt,
            max_tokens=100,
            nft=True
        )
        image_url = response.choices[0].text
        image_data = requests.get(image_url).content
        return image_data
    except Exception as e:
        logging.error(f"Failed to generate image with prompt '{prompt}': {str(e)}")
        return None


# Define function to generate poem with GPT-3
def generate_poem(prompt: str) -> str or None:
    """Generates a poem using the GPT-3 OpenAI API, given a prompt string.

        Args:
            prompt (str): The prompt string to use for generating the poem.

        Returns:
            str or None: The generated poem text, or None if an error occurred.

        """
    try:
        response = openai.Completion.create(
            engine="davinci",
            prompt=prompt,
            max_tokens=200
        )
        poem = response.choices[0].text
        return poem
    except Exception as e:
        logging.error(f"Failed to generate poem with prompt '{prompt}': {str(e)}")
        return None


# Define function to handle new mentions or direct messages
class MyStreamListener(tweepy.StreamListener):
    """Handles new mentions or direct messages that contain the '@TwAI' handle.

        When a new mention or direct message is received, the handle extracts the message text, generates an image and a poem
        using the generate_image() and generate_poem() functions, and posts the result as a reply to the original message.

        """

    def on_status(self, status: tweepy.Status) -> None:
        """Called when a new status (i.e. tweet or direct message) is received.

               If the status is a mention or direct message that contains the '@TwAI' handle, the function extracts the message
               text, generates an image and a poem using the generate_image() and generate_poem() functions, and posts the result
               as a reply to the original message.

               Args:
                   status (tweepy.Status): The status object representing the new message.

               Returns:
                   None

               """
        if status.in_reply_to_screen_name == "TwAI":
            # Extract text of the message
            message_text = status.text.split(' ')[1:]

            # Generate image with DALL-E
            image_data = generate_image(' '.join(message_text))
            if image_data is None:
                return
            image_file = io.BytesIO(image_data)

            # Generate poem with GPT-3
            poem_text = generate_poem(' '.join(message_text))
            if poem_text is None:
                return

            # Post image and poem to Twitter
            try:
                media = api.media_upload(filename='image.jpg', file=image_file)
                api.update_status(status=poem_text, in_reply_to_status_id=status.id, media_ids=[media.media_id])
                logging.info(f"Posted poem and image in response to tweet {status.id}")
            except Exception as e:
                logging.error(f"Failed to post poem and image in response to tweet {status.id}: {str(e)}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    myStream.filter(track=['@TwAI'])  # Listen for tweets that mention "@TwAI"
