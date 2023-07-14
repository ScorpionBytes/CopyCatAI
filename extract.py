import sys, os
import re
import requests
from PIL import Image
from base64 import b64decode
from PIL import ImageGrab, Image
from bs4 import BeautifulSoup
import pytesseract


tesseract_path_mac = os.path.join("/opt/homebrew/bin/", "tesseract")
tesseract_path_windows = os.path.join("C:/Program Files/Tesseract-OCR/tesseract.exe")
tesseract_path_linux = os.path.join("/usr/bin/tesseract")

# Set the tesseract command path based on the current operating system
if sys.platform == 'darwin':
    pytesseract.pytesseract.tesseract_cmd = tesseract_path_mac
elif sys.platform == 'win32':
    pytesseract.pytesseract.tesseract_cmd = tesseract_path_windows
elif sys.platform.startswith('linux'):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path_linux

def get_image_from_clipboard():
    if os.path.exists("/tmp/copycat.jpg"):
        os.remove("/tmp/copycat.jpg")

    img = ImageGrab.grabclipboard()

    # <PIL.JpegImagePlugin.JpegImageFile image mode=RGB size=200x71 at 0x105E68700>

    if not isinstance(img, Image.Image):
        return False
    else:
        img.save("/tmp/copycat.jpg")
        return True


# List of supported file formats
supported_file_formats = [
    ".csv",
    ".doc",
    ".docx",
    ".eml",
    ".epub",
    ".gif",
    ".htm",
    ".html",
    ".jpeg",
    ".jpg",
    ".json",
    ".log",
    ".mp3",
    ".msg",
    ".odt",
    ".ogg",
    ".pdf",
    ".png",
    ".pptx",
    ".ps",
    ".psv",
    ".rtf",
    ".tab",
    ".tff",
    ".tif",
    ".tiff",
    ".tsv",
    ".txt",
    ".wav",
    ".xls",
    ".xlsx",
]


def qr_extract(img_path):
    # Read the QR code
    data = decode(Image.open(img_path))
    data = "".join(d.data.decode("utf-8") for d in data)

    return data


def remove_html_and_js(html):
    html = re.sub(r"<[^>]*>", "", html)
    html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    return html


def first_sentence(sentence):
    # Split the string into a list of words
    words = sentence.split()

    # Loop through the list
    for word in words:
        # Check for the end of the sentence
        if word[-1] in (".", "!", "?", ";", ":", "...", "\n"):
            # Stop parsing
            break
    # Return the first sentence
    return " ".join(words[: words.index(word) + 1])


def isLink(text):
    link_pattern = r'^https?://[^\s<>"]+|www\.[^\s<>"]+'
    return re.search(link_pattern, text)


def extracturl(text):
    """
    Extracts URLs from the given text.

    Parameters:
        text (str): The text to extract URLs from

    Returns:
        str: The extracted URL
    """
    match = re.search(r"(https?://\S+)", text)
    if match:
        return match.group(0)
    else:
        return None


def parse_html_to_text(html):
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()  # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)

    return text


def get_page_from_text(user, text, nospace=False):
    print("Getting page from text")
    HTML = False
    file_path = "/tmp/" + str(user) + "-page.txt"
    # Use regular expression to search for patterns that match a URL
    link_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    match = re.search(link_pattern, text)
    # Check if there is a match
    if match:
        print("Found a match!")
        # Extract the link
        link = match.group()
        # Use requests library to get the main page of the website, following redirects
        page = requests.get(link, allow_redirects=True)
        print(type(page.content))
        # Download the page
        with open(file_path, "wb") as file:
            print("Downloading page...", file_path)
            if page.headers[
                "Content-Type"
            ] == "text/html" or page.headers["Content-Type"] == "text/html; charset=utf-8":
                print("HTML document")
                file.write(parse_html_to_text(page.content).encode())

                HTML = True
                print("HTML")
            else:
                print("Not HTML")
                file.write(page.content)
        print("Successfully downloaded page!")
        # Return the page text
        if not HTML:
            text = basic_text_extractor(file_path)
        if HTML:
            text = open(file_path, "rb").read().decode()
        os.remove(file_path)
        return text
    else:
        try:
            os.remove(file_path)
        except:
            pass
        return "".strip()


def basic_text_extractor(file_path):
    """
    Extracts text from the file.
    Args:
        file_path (str): Path to the file.
    Returns:
        str: Extracted text from the file.
    Raises:
        ValueError: If the file format is not supported.
    """
    # Check if the file format is supported

    # Reads the file content
    # CMD = "/opt/homebrew/bin/tesseract " + file_path + " /tmp/out"
    # subprocess.Popen(CMD, shell=True).wait()
    text = pytesseract.image_to_string(Image.open(file_path))

    # Converts the file content to string format
    # text = open("/tmp/out.txt", "r").read()

    # Returns the text extracted from the file
    return text


# Define the Bearer token
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAHAzlQEAAAAAbHxUwV9fuz77UEJid4AWPzgyb6M%3DCKfnk0FtXHb7xf9rbwTzRqUB55a2oKwDHKnxYVPAbTCiL2NPEo"


# define search twitter function
def search_twitter(url, bearer_token=BEARER_TOKEN):
    dataset = []

    tweet_fields = "tweet.fields=text,created_at"
    match = re.search("(www.)?twitter.com/(?P<user>[^/]+)", url)

    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    if match:
        user = match.group("user")
        # Use the user's screen name or user ID to construct the query
        query = f"from:{user}"
        url = "https://api.twitter.com/2/tweets/search/recent?query={}&{}".format(
            query, tweet_fields
        )

    else:
        return "Invalid Twitter User URL. Please enter a valid Twitter User"

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        return "There doesn't seem to be any twitter data for this user."
    resp = response.json()
    for data in resp["data"]:
        dataset += [data["text"]]
    return "\n".join(dataset)


def isTwitterLink(url):
    """
    Checks whether a given URL is for Twitter or not.

    Parameters:
        url (str): The URL to be checked

    Returns:
        bool: True if the URL is for Twitter, False otherwise
    """
    if not isinstance(url, str):
        return False
    return url.startswith("https://www.twitter.com") or url.startswith(
        "https://twitter.com"
    )
