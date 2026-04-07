import openai
import base64

from parse_voice import parse_voice

class Model:
    def __init__(self,keyfile="secrets/apikey.txt",preamble="Draw a 2d top down map, for a TTRPG, based on the following description, given by the game master to the players. Ignore and do not include any people, creatures or animals."):

        with open(keyfile,"r") as key_file:
            apikey = key_file.read()

        self.preamble = preamble
        self._client = openai.OpenAI(api_key=apikey)

    def generate_from_text(self,prompt):
        return self._client.responses.create(
            model = "gpt-5-mini",
            input =  self.preamble + prompt,
            tools = [{"type" : "image_generation"}]
        )

    def generate_from_voice(self,wave_file):
        return self.generate_from_text(parse_voice(wave_file))


if __name__ == "__main__":

    gpt_model = Model()

    response = gpt_model.generate_from_text("You enter a tavern by a door on on the west side. At bar along the south wall where an orc barman is cleaning glasse. Patrons sit at tables scattered around the room. A hooded stranger sits alone at a table in the corner")

    print(list(response.output))

    image_data = [
        output.result
        for output in response.output
        if output.type == "image_generation_call"
    ]
    
    if image_data:
        for (i,img) in enumerate(image_data):
            with open(f"outputs/tavern{i}.png", "wb") as f:
                f.write(base64.b64decode(img))