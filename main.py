import logging

logger = logging.getLogger('disnake')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='disnake.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

print("Starting Discboom!")
print("Importing Modules...")
import disnake
import string
import asyncio
import os.path
import pickle
import pandas as pd

from dotenv import load_dotenv
from disnake.ext import commands
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

intents = disnake.Intents(message_content=True, reactions=True, messages=True, emojis=True)

print("Importing .env Config...")

scopes = ['https://www.googleapis.com/auth/spreadsheets']

load_dotenv()

disc_token = os.getenv('DISCORD_TEST_TOKEN')
sh_id = os.getenv('SPREADSHEET_ID')
data_to_pull = os.getenv('RANGE')

print("Initializing Google Authentication...")

def gsheet_api_check(scopes):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client.secrets.json', scopes)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


# Function used to pull sheet data
def pull_sheet_data(SCOPES, sh_id, data_to_pull):
    creds = gsheet_api_check(SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=sh_id,
        range=data_to_pull).execute()
    values = result.get('values', [])


    if not values:
        print('No data found.')
    else:
        rows = sheet.values().get(spreadsheetId=sh_id,
                                  range=data_to_pull).execute()
        data = rows.get('values')
        print("COMPLETE: Data copied")
        return data

number = 1
data = pull_sheet_data(scopes,sh_id,data_to_pull)
df = pd.DataFrame(data[1:], columns=data[0])

bot = commands.Bot(command_prefix='/', sync_commands_debug=False, intents=intents)
#test_guilds=[854584529229578260], This line can be put in the line above to test in specific server

# Print to console when bot has connected to discord
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# @bot.slash_command(description=f'Updates the database if you\'re a dev.')
# async def update(inter):
#     response = "The Dataframe has been updated."
#     data = pull_sheet_data(scopes, sh_id, data_to_pull)
#     df = pd.DataFrame(data[1:], columns=data[0])
#     print(df)
#     #response = "You must be registered as a dev/tester to use this command."
#     await inter.response.send_message(f'{response}\n{df}')

@bot.command(name='esp', help='Please get your server owner to reinvite Discboom!')
async def esp(inter):
    response = "Discboom has been updated to use discord's slash commands! To make sure the bot works correctly, please have your server" \
               "owner reinvite Discboom using this link: https://discord.com/api/oauth2/authorize?client_id=982371593655316480&permissions=414464699456&scope=bot%20applications.commands"
    await inter.send(response)

@bot.slash_command(description='Prints a picture of the elemental strength/weakness chart')
async def elements(inter):
    response = "https://cdn.playdislyte.com/wp-content/uploads/2021/10/Dislyte-Elemental-Classes-and-the-Countering-System.png"
    await inter.response.send_message(response)

@bot.slash_command(description="Shows esper tier list position and corresponding information")
async def esp(inter, *, esp_name):

    print(f'Start of search')

    # List of emoji choices
    esp_name = "".join(esp_name)
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
    icons_list = ['https://cdn.discordapp.com/attachments/910693332856995902/983583089693437982/Shimmer.png',
             'https://cdn.discordapp.com/attachments/910693332856995902/983583104251879454/Wind.png',
             'https://cdn.discordapp.com/attachments/910693332856995902/983583075793502269/Flow.png',
             'https://cdn.discordapp.com/attachments/910693332856995902/983583081506177054/Inferno.png']

    element_list = ['Shimmer', 'Wind', 'Flow', 'Inferno']
    colors = {'Shimmer':0x9BFDFE, 'Wind':0x1CF0BF, 'Flow':0xDC78FE,'Inferno':0xFF8C00}

    # Used to compare user string to DataFrame
    if len(df.index[df['ESPER_DIETY'].str.contains(string.capwords(esp_name))].tolist()) > 0:
        pos_list = (df.index[df['ESPER_DIETY'].str.contains(string.capwords(esp_name))].tolist())
        temp_list = (df.index[df['ESPER_NAME'].str.contains(string.capwords(esp_name))].tolist())
        pos_list.extend(temp_list)
    else:
        pos_list = (df.index[df['ESPER_NAME'].str.contains(string.capwords(esp_name))].tolist())

    # Create author variable for multiple_results_emb
    author = inter.author

    # If no results, tell user
    if (len(pos_list) == 0):
        await inter.response.send_message(f'No esper results were found for {esp_name}')
    
    # If multiple results, print multiple results embed
    if (len(pos_list) > 1):
        multiple_espers = True
        multiple_results_emb = disnake.Embed(
            title=f'Boomboom has returned multiple esper results!',
            description=f'Please select which esper you\'re looking for',
            colour=0x9080F2
        )
        multiple_results_emb.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/983263319341285457/983602199655514132/unknown.png')
        
        # Timeout embed for if no reaction is added within 30sec
        timeout_embed = disnake.Embed(
            title=f'Boomboom only waits 30 seconds for a reaction...',
            description=f'There are other users he needs to help too!',
            colour=disnake.Colour.red()
        )
        timeout_embed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/449419840101285907/983966721331314748/Boomboom_Cry.png')

        n = 1 # Used to keep track of number of choices
        for esp in pos_list:
            multiple_results_emb.add_field(name=f'{n}:', value=f"{df['ESPER_NAME'].iloc[esp]} ({df['ESPER_DIETY'].iloc[esp]})", inline=True)
            n+=1

        #Print multiple_results_emb and set emb to original message
        await inter.send(embed = multiple_results_emb)
        emb = await inter.original_message()

        #Loop to add reactions to embed
        for emoji in emojis[0:len(pos_list)]:
            await emb.add_reaction(emoji)

        #Check
        def check(reaction, user):
            return user == author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']

        #If check fails, edit the multiple results embed to the timeout embed and relete reactions
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            await emb.edit(embed=timeout_embed)
            await emb.clear_reactions()

        #Set esper position to reaction choice
        if str(reaction) == "1️⃣":
            es_pos = pos_list[0]
        elif str(reaction) == "2️⃣":
            es_pos = pos_list[1]
        elif str(reaction) == "3️⃣":
            es_pos = pos_list[2]
        elif str(reaction) == "4️⃣":
            es_pos = pos_list[3]
        elif str(reaction) == "5️⃣":
            es_pos = pos_list[4]

        #Clear reactions on embed
        await emb.clear_reactions()
    else:
        multiple_espers=False
        
        # Convert pos_list var from list to int
        strings = [str(integer) for integer in pos_list]
        a_string = "".join(strings)
        es_pos = int(a_string)


    # Get all esper information from tier list sheet and store in variables - I am sorry there are so many
    tl_name = df['ESPER_NAME'].iloc[es_pos]
    tl_diety = df['ESPER_DIETY'].iloc[es_pos]
    tl_stars = df['RARITY'].iloc[es_pos]
    tl_role = df['ROLE'].iloc[es_pos]
    tl_sum = df['SUMMARY'].iloc[es_pos]
    tl_icon = df['ICON_URL'].iloc[es_pos]
    tl_rank = df['OVERALL_RANK'].iloc[es_pos]
    tl_role_rank = df['ROLE_RANK'].iloc[es_pos]
    tl_element = (int(df['ELEMENT'].iloc[es_pos]))
    tl_story = df['STORY'].iloc[es_pos]
    tl_cube = df['CUBE'].iloc[es_pos]
    tl_kronos = df['KRONOS'].iloc[es_pos]
    tl_apep = df['APEP'].iloc[es_pos]
    tl_fafnir = df['FAFNIR'].iloc[es_pos]
    tl_temp_tower = df['TOWER'].iloc[es_pos]
    tl_point_war_def = df['POINT_DEF'].iloc[es_pos]
    tl_point_war_atk = df['POINT_ATK'].iloc[es_pos]
    tl_overall_rating = df['RANK_SCORE'].iloc[es_pos]
    tl_4_set_relic = df['RELIC_4'].iloc[es_pos]
    tl_2_set_relic = df['RELIC_2'].iloc[es_pos]
    tl_una_ii = df['UNA_II'].iloc[es_pos]
    tl_una_iv = df['UNA_IV'].iloc[es_pos]
    tl_mui_ii = df['MUI_II'].iloc[es_pos]
    # tl_captain = df['CAPTAIN'].iloc[es_pos]
    # tl_atk_base = df['ATK_BASE'].iloc[es_pos]
    # tl_hp_base = df['HP_BASE'].iloc[es_pos]
    # tl_def_base = df['DEF_BASE'].iloc[es_pos]
    # tl_spd_base = df['SPD_BASE'].iloc[es_pos]

    # GENERATE PAGES...
    # PAGE 1 OF ESPER INFO (tiers)

    tier_embed = disnake.Embed(
        title=f'{tl_name} ({tl_diety})',
        url=f'https://dislyte.fandom.com/wiki/{tl_name.replace(" ", "_")}_({tl_diety.replace(" ", "_")})',
        description=f'{tl_stars} :star: {tl_role}',
        color=colors[f'{element_list[int(tl_element)]}']
    )

    tier_embed.set_author(name=f'Esper Info: Tiers', icon_url=f'{icons_list[int(tl_element)]}')
    tier_embed.set_thumbnail(url=f'{tl_icon}')
    tier_embed.add_field(name='Overall Rank', value=f'#{tl_rank}', inline=True)
    tier_embed.add_field(name=f'{tl_role} Rank', value=f'#{tl_role_rank}', inline=True)
    tier_embed.add_field(name='Power Score', value=f'{tl_overall_rating}', inline=True)
    tier_embed.add_field(name='Description', value=f'{tl_sum}', inline=False)
    tier_embed.add_field(name='Story', value=f'{tl_story}', inline=True)
    tier_embed.add_field(name='Cube', value=f'{tl_cube}', inline=True)
    tier_embed.add_field(name='Tower', value=f'{tl_temp_tower}', inline=True)
    tier_embed.add_field(name='Kronos', value=f'{tl_kronos}', inline=True)
    tier_embed.add_field(name='Apep', value=f'{tl_apep}', inline=True)
    tier_embed.add_field(name='Fafnir', value=f'{tl_fafnir}', inline=True)
    tier_embed.add_field(name='Point War (DEF)', value=f'{tl_point_war_def}', inline=True)
    tier_embed.add_field(name='Point War (ATK)', value=f'{tl_point_war_atk}', inline=True)
    tier_embed.set_footer(text="Please report any bugs here! https://discord.gg/ttsVvYMxyA",
                          icon_url='https://cdn.discordapp.com/attachments/449419840101285907/983977795225010216/Discboom.png')


    # PAGE 2 OF ESPER INFO (relics)

    relic_embed = disnake.Embed(
        title=f'{tl_name} ({tl_diety})',
        url=f'https://dislyte.fandom.com/wiki/{tl_name.replace(" ", "_")}_({tl_diety.replace(" ", "_")})',
        description=f'{tl_stars} :star: {tl_role}',
        color=colors[f'{element_list[int(tl_element)]}']
    )

    relic_embed.set_author(name=f'Esper Info: Relics', icon_url=f'{icons_list[int(tl_element)]}')
    relic_embed.set_thumbnail(url=f'{tl_icon}')
    relic_embed.add_field(name='Description', value=f'{tl_sum}', inline=False)
    relic_embed.add_field(name='4-set Relic', value=f'{tl_4_set_relic}', inline=False)
    relic_embed.add_field(name='2-set Relic', value=f'{tl_2_set_relic}', inline=False)
    relic_embed.add_field(name='UNA I', value='ATK', inline=True)
    relic_embed.add_field(name='UNA III', value='DEF', inline=True)
    relic_embed.add_field(name='MUI I', value='HP', inline=True)
    relic_embed.add_field(name='UNA II', value=f'{tl_una_ii}', inline=True)
    relic_embed.add_field(name='UNA IV', value=f'{tl_una_iv}', inline=True)
    relic_embed.add_field(name='MUI II', value=f'{tl_mui_ii}', inline=True)
    relic_embed.set_footer(text="Please report any bugs here! https://discord.gg/ttsVvYMxyA",
                          icon_url='https://cdn.discordapp.com/attachments/449419840101285907/983977795225010216/Discboom.png')

    # PRINT EMBEDS
    if multiple_espers:
        info_emb = await emb.edit(embed=tier_embed)
    else:
        await inter.response.send_message(embed=tier_embed)
        info_emb = await inter.original_message()

    await info_emb.add_reaction('▶')

    def check2(reaction, user):
        return user == author and str(reaction.emoji) in ['▶', '◀'] and info_emb.id == reaction.message.id

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30, check=check2)
    except asyncio.TimeoutError:
        await info_emb.clear_reactions()

    active = 1
    while active == 1:
        if str(reaction) == "▶":
            await info_emb.clear_reactions()
            await info_emb.edit(embed=relic_embed)
            await info_emb.add_reaction('◀')

            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=30, check=check2)
            except asyncio.TimeoutError:
                active = 0
                await info_emb.clear_reactions()

        elif str(reaction) == "◀":
            await info_emb.clear_reactions()
            await info_emb.edit(embed=tier_embed)
            await info_emb.add_reaction('▶')

            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=30, check=check2)
            except asyncio.TimeoutError:
                active = 0
                await info_emb.clear_reactions()

    print(f'I have finished this /esp search')


@bot.slash_command(description="Sends an invite to the official Dislyte discord server")
async def disc(inter):
    response = "https://discord.com/invite/dislyte"
    await inter.response.send_message(response)

@bot.slash_command(description="Sends an invite to the Discboom bot discord server")
async def bothelp(inter):
    response = "https://discord.com/invite/cMrbjdrgy9"
    await inter.response.send_message(response)

@bot.slash_command(description="invite Discboom to your own server")
async def invite(inter):
    response = "https://discord.com/api/oauth2/authorize?client_id=982371593655316480&permissions=414464699456&scope=bot%20applications.commands"
    await inter.response.send_message(response)

@bot.slash_command(description="Prints a list of the active disltye gift codes!")
async def codes(inter):
    response = "__**Current active gift codes are:**__\nDislyteytb50k \nJontronShow\nLingBigYong\nJoinDislyte\nAviveHD\nStSkiCrimax\nTGTyoutube\n\nYou can redeem your codes here: https://cdkey.farlightgames.com/dislyte-global\n\n*Please do let me know if any are expired so that I can change them!*"
    await inter.response.send_message(response)

@bot.slash_command(description="A list of contributors to the bot and sources for all of our information")
async def contributors(inter):
    response = "__Esper info:__ https://docs.google.com/spreadsheets/d/15hc3Nx6TDS7BNAIXid0gNO1j7gcVeydNoLwyY4POtzc/edit?usp=sharing\n" \
               "__Holobattle information:__ <@201123494346489856>"
    await inter.response.send_message(response)

@bot.slash_command(description="Helpful information about the holobattle system")
async def holo(inter):
    response = "**__How Holobattle Works__**\n" \
               "You always fight a different team than you defend against\n" \
               "If your team meets the shown point threshold in 48 hours, your team wins!\n" \
               "If your team can not meet that threshold, your team loses.\n" \
               "__**Trophy color values**__\n" \
               "Gold: 500 points for each round, totaling 1000 possible points for both round wins\n" \
               "Pink: 250 points for each round, totaling 500 possible points for both round wins\n" \
               "Blue: 125 points for each round, totaling 250 possible points for both round wins\n" \
               "If you happen to attack a player with half of a trophy color left, you'll only get-\n " \
               "the points for the half trophy color for one of the rounds, and the next highest trophy value for the other round.\n\n" \
               "*Holobattle information provided by <@201123494346489856> - May be updated in the future*"
    await inter.response.send_message(response)

@bot.slash_command(description="Display a list of bot commands")
async def help(inter):
    response = '/holo: Helpful information about the holobattle system\n' \
               '/contributors: A list of contributors to the bot and sources for all of our information\n' \
               '/codes: Prints a list of the active disltye gift codes!\n' \
               '/invite: invite Discboom to your own server\n' \
               '/bothelp: Sends an invite to the Discboom bot discord server\n' \
               '/disc: Sends an invite to the official Dislyte discord server\n' \
               '/esp: Shows esper tier list position and corresponding information\n' \
               '/elements: Prints a copy of the elemental strengths and weaknesses chart'
    await inter.response.send_message(response)

@esp.error
async def tl_error(inter, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await inter.response.send_message('Please specify an esper')

bot.run(disc_token)