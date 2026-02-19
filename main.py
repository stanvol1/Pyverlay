import re
from textual.app import App
from textual.widgets import Footer, Header, DataTable
from rich.text import Text
import requests

# Define rows for overlay, might expand this at some point for anti sniping features
ROWS = ["Name", "Final kills", "Final deaths", "FKDR", "Winstreak"]

# Overlay class, need to make it look better
class Overlay(App):
    def __init__(self):
        super().__init__()
        self.unknown = Text("UNKNOWN", style = "red")
        self.players = []
        self.log_file = ""
        self.word = "ONLINE:"
        self.api_key = ""
        self.urchin_api = ""
        self.cache = {}
        self.urchin_cache = {}
        self.session = requests.Session()

    def compose(self):
        yield Header()
        yield DataTable()
        yield Footer()


    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Name", "Tag", "Level", "Final kills", "Final deaths", "FKDR", "Winstreak")
        self.find_players()
        self.set_interval(2, self.find_players)

    def get_info(self, call):
        r = self.session.get(call, timeout = 5)
        return r.json()

    def find_players(self):
        self.players = []

        with open(self.log_file, 'r') as file_:
            line_list = list(file_)

            line = None

            for number in line_list:
                if number.find('ONLINE:') != -1:
                    line = number
            if line:
                clean1 = line.strip("[")
                clean2 = clean1.replace("[Client thread/INFO]: [CHAT] ONLINE:", "")
                clean3 = re.sub(r"\d+]", "", clean2)
                clean4 = re.sub(r"\d+:", "", clean3)
                player_names = clean4.lstrip().replace(",", "").strip("\n")

                new_players = set(player_names.split())

                if new_players != set(self.players):
                    self.players = (player_names.split())
                    self.player_watch()

    def player_watch(self):
        global tag
        new = False
        table = self.query_one(DataTable)
        table.clear()
        for i in self.players:
            if i in self.cache:
                data = self.cache[i]
                self.urchin_data = self.urchin_cache[i]

            else:

                try:
                    url = f'https://api.mojang.com/users/profiles/minecraft/{i}?'
                    response = self.session.get(url)
                    self.uuid = response.json()['id']
                    urchin_url = f"https://urchin.ws/cubelify?id={self.uuid}&name={self.uuid}&sources=GAME&key={self.urchin_api}"
                    self.uuid_link = f"https://api.hypixel.net/player?key={self.api_key}&uuid={self.uuid}"
                    self.urchin_data = self.get_info(urchin_url)
                    data = self.get_info(self.uuid_link)
                    self.cache[i] = data
                    self.urchin_cache[i] = self.urchin_data

                except Exception:
                    table.add_row(i, Text("NICK", style = "green"), self.unknown, self.unknown, self.unknown, self.unknown, self.unknown)
                    continue

            sniper = False
            tag = "---"

            try:
                urchin_tag = self.urchin_data["tags"][0]
                if "Sniper" in urchin_tag.get("tooltip", 0):
                    sniper = True
                else:
                    sniper = False
            except KeyError:
                pass
            try:
                stats = data["player"]["stats"]["Bedwars"]
                player_stats = data["player"]
                final_kills = stats.get("final_kills_bedwars", 0)
                final_deaths = stats.get("final_deaths_bedwars", 0)
                experience = stats.get("Experience", 0)
                winstreak = stats.get("winstreak", 0)
                new = False

            except:
                new = True
                stats = "Error"
                player_stats = "Error"
                final_kills = 0
                final_deaths = 0
                experience = 0
                winstreak = 0


            colour = "gray"
            dev = str(i) == "stanvol"


            try:
                fkdr = int(final_kills) / int(final_deaths)
            except ZeroDivisionError:
                fkdr = int(final_kills) / 1

            level = (float(experience) / (96 * 5000 + 7000)) * 100
            fkdr_colour = "gray"

            if fkdr >= 2.99:
                fkdr_colour = "red"

            elif fkdr >= 2.99:
                fkdr_colour = "yellow"

            elif fkdr >= 0.99:
                fkdr_colour = "green"

            try:
                channel = player_stats.get("channel", 0)

            except Exception:
                channel = "Not found"

            ## Tag colouring ##

            tag = "---"

            if sniper:
                tag = "SNIPR"
                colour = "red"

            elif new:
                tag = "NEW"


            if fkdr >= 3.5 and level < 50.0 or fkdr >= 5 and level < 100 and not sniper:
                tag = "ALT"
                colour = "orange1"

            elif channel == "PARTY" and not sniper and not dev:
                tag = "PARTY"
                colour = "blue"

            elif str(i) == "stanvol":
                tag = "DEV"
                colour = "purple"

            styled_tag = Text(tag, style = colour)
            styled_fkdr = Text(str(round(fkdr, 3)), style = fkdr_colour)

            table.add_row( i, styled_tag, int(round(level, 0)), final_kills, final_deaths, styled_fkdr, winstreak)

# https://urchin.ws/cubelify?id={uuid}name={uuid}}&sources=GAME&key=aeff7a1d-212e-421c-b1dd-2049fc9f3850

if __name__ == "__main__":
    overlay_instance = Overlay()
    overlay_instance.run()