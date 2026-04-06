import openai
import base64

with open("secrets/apikey.txt","r") as key_file:
    apikey = key_file.read()

client = openai.OpenAI(api_key=apikey)

response = client.responses.create(
    model = "gpt-5-mini",
    input = "Draw a 2d top down map based on the following description. Ignore and do not include any people, creatures or animals. You enter a tavern with a bar along the north wall, a door and windows on the west wall and 3 tables, with chairs.",
    tools = [{"type" : "image_generation"}]
)

print(list(response.output))

image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]
    
if image_data:
    image_base64 = image_data[0]
    with open("outputs/tavern.png", "wb") as f:
        f.write(base64.b64decode(image_base64))