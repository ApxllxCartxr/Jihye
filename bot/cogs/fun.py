from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from urllib.request import urlopen
import textwrap
import fast_colorthief 
import wcag_contrast_ratio as contrast





import disnake
from disnake.ext import commands





class fun(commands.Cog):
    """Contains all the cmds related to fun stuff"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def spoti(self, ctx, user: disnake.Member = None):
        user = user or ctx.author
        for activity in user.activities:
            if isinstance(activity, disnake.Spotify):
                basewidth = 220
                img = Image.open(urlopen(activity.album_cover_url))
                wpercent = basewidth / float(img.size[0])
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), Image.ANTIALIAS)
                
                regular = ImageFont.truetype(
                    font="fonts/HandotrialBold-ALX8M.otf", size=65
                )
                thin = ImageFont.truetype(
                    font="fonts/HandotrialRegular-jE87G.otf", size=35
                )

                fd = urlopen((activity.album_cover_url))
                f = BytesIO(fd.read())
                bg = fast_colorthief.get_dominant_color(f,quality=1)
                colors = fast_colorthief.get_palette(f,color_count=6)
                
                # im = Image.new(mode="RGB", size=(1000, 300), color=fast_colorthief.get_dominant_color(f,quality=1))
                # draw = ImageDraw.Draw(im=im)
                # Image.Image.paste(im, img, (30, 40))
                song = textwrap.shorten(activity.title, width=20, placeholder="...")
                artists = textwrap.shorten(', '.join(activity.artists), width=35, placeholder="...")
                for i, color in enumerate(colors):
                    cont = contrast.rgb(bg, color)
                    if contrast.passes_AAA(cont):
                        im = Image.new(mode="RGB", size=(1000, 300), color=bg)
                        draw = ImageDraw.Draw(im=im)
    
                        draw.text(
                            xy=(280, 110),
                            text=f"{activity.album}",
                            font=thin,
                            fill=color,
                            anchor="ls",
                        )
                        draw.text(
                            xy=(280, 170),
                            text=f"{song}",
                            font=regular,
                            fill=color,
                            anchor="ls",
                        )
                        draw.text(
                            xy=(280,210),
                            text=f"by {artists}",
                            font=thin,
                            fill=color,
                            anchor="ls",
                        )
                        Image.Image.paste(im, img, (30, 40))           
                        with BytesIO() as image_binary:
                            im.save(image_binary, "PNG")
                            image_binary.seek(0)
                            await ctx.send(
                                file=disnake.File(fp=image_binary, filename="image.png")
                            )
                    else:
                        continue

def setup(bot):
    bot.add_cog(fun(bot))
