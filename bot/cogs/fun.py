from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from urllib.request import urlopen

import disnake
from disnake.ext import commands


class fun(commands.Cog):
    """Contains all the cmds related to autoresponders"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def no(self, ctx, user: disnake.Embed = None):
        user = user or ctx.author
        for activity in user.activities:
            if isinstance(activity, disnake.Spotify):
                await ctx.send(
                    f"{user} is listening to {activity.title} by {activity.artist}"
                )
                basewidth = 250
                img = Image.open(urlopen(activity.album_cover_url))
                wpercent = basewidth / float(img.size[0])
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), Image.ANTIALIAS)

                bold = ImageFont.truetype(
                    font="fonts/LemonMilkMedium-mLZYV.otf", size=70
                )
                # regular = ImageFont.truetype(
                #     font="fonts/LemonMilkMedium-mLZYV.otf", size=45
                # )
                thin = ImageFont.truetype(
                    font="fonts/LemonMilkRegular-X3XE2.otf", size=35
                )
                im = Image.new(mode="RGB", size=(1000, 300), color="#24242c")
                draw = ImageDraw.Draw(im=im)
                # draw.text(
                #     xy=(450, 79),
                #     text="THE BADDEST",
                #     font=regular,
                #     fill="#bbcce3",
                #     anchor="mm",
                # )
                draw.text(
                    xy=(550, 150),
                    text=f"{activity.title}",
                    font=bold,
                    fill="#bbcce3",
                    anchor="mm",
                )

                draw.text(
                    xy=(550, 210),
                    text=f"By {activity.artist}",
                    font=thin,
                    fill="#bbcce3",
                    anchor="mm",
                )

                Image.Image.paste(im, img, (30, 30))
                with BytesIO() as image_binary:
                    im.save(image_binary, "PNG")
                    image_binary.seek(0)
                    await ctx.send(
                        file=disnake.File(fp=image_binary, filename="image.png")
                    )


def setup(bot):
    bot.add_cog(fun(bot))
