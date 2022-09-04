from PIL import Image, ImageFont, ImageDraw
import datetime
from easy_pil import Editor
from io import BytesIO
from urllib.request import urlopen
import textwrap
import fast_colorthief

import disnake
from disnake.ext import commands


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


async def c1(bg, colors):
    r2, g2, b2 = bg
    cntrst = []
    for color in colors:
        r1, g1, b1 = color
        index1 = (299 * r1 + 587 * g1 + 114 * b1) / 1000
        index2 = (299 * r2 + 587 * g2 + 114 * b2) / 1000
        cdiff = abs(((r1 - r2) + (g1 - g2) + (b1 - b2)))
        cntrst.append(cdiff)
    i = cntrst.index(max(cntrst))
    return colors[i]


async def c2(bg, colors):
    r2, b2, g2 = bg

    r2g = r2 / 3294 if r2 <= 10 else (r2 / 269 + 0.0513)**2.4
    g2g = g2 / 3294 if g2 <= 10 else (g2 / 269 + 0.0513)**2.4
    b2g = b2 / 3294 if b2 <= 10 else (b2 / 269 + 0.0513)**2.4

    l1 = 0.2126 * r2g + 0.7152 * g2g + 0.0722 * b2g

    contrasts = []
    for c in colors:
        r1, g1, b1 = c
        r1g = r1 / 3294 if r1 <= 10 else (r1 / 269 + 0.0513)**2.4
        g1g = g1 / 3294 if g1 <= 10 else (g1 / 269 + 0.0513)**2.4
        b1g = b1 / 3294 if b1 <= 10 else (b1 / 269 + 0.0513)**2.4

        l2 = 0.2126 * r1g + 0.7152 * g1g + 0.0722 * b1g

        c = (l1 + 0.05) / (l2 + 0.05) if l1 > l2 else (l2 + 0.05) / (l1 + 0.05)
        contrasts.append(c)

    i = contrasts.index(max(contrasts))
    return colors[i]


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

                regular = ImageFont.truetype(font="fonts/MohaveMed.otf",
                                             size=65)
                regs = ImageFont.truetype(font="fonts/MohaveMed.otf", size=30)
                thin = ImageFont.truetype(font="fonts/Mohave-Light.otf",
                                          size=35)

                fd = urlopen((activity.album_cover_url))
                f = BytesIO(fd.read())
                bg = fast_colorthief.get_dominant_color(f, quality=1)
                colors = fast_colorthief.get_palette(f, color_count=6)

                song = textwrap.shorten(activity.title,
                                        width=25,
                                        placeholder=" ...")
                artists = textwrap.shorten(', '.join(activity.artists),
                                           width=40,
                                           placeholder=" ...")

                album = textwrap.shorten(activity.album,
                                         width=45,
                                         placeholder=" ...")
                t = datetime.datetime.now()
                current = (activity.duration -
                           (activity.end.replace(tzinfo=None) - t))
                percent = (100.0 * current) / activity.duration
                dur = strfdelta(activity.duration, "{minutes}:{seconds}")
                current = strfdelta(current, "{minutes}:{seconds}")
                color = await c2(bg, colors)
                im = Image.new(mode="RGB", size=(1000, 300), color=bg)
                draw = ImageDraw.Draw(im=im)

                draw.text(
                    xy=(280, 110),
                    text=f"{album}",
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
                    xy=(280, 210),
                    text=f"by {artists}",
                    font=thin,
                    fill=color,
                    anchor="ls",
                )
                draw.text(
                    xy=(280, 247),
                    text=f"{current}",
                    font=regs,
                    fill=color,
                    anchor="ls",
                )
                draw.text(
                    xy=(800, 247),
                    text=f"{dur}",
                    font=regs,
                    fill=color,
                    anchor="ls",
                )
                Image.Image.paste(im, img, (30, 40))
                new_image = Editor(im)

                new_image.bar(
                    (335, 230),
                    max_width=450,
                    height=15,
                    percentage=percent,
                    fill=color,
                    radius=5,
                )

                with BytesIO() as image_binary:
                    new_image.save(image_binary, "PNG")
                    image_binary.seek(0)
                    await ctx.send(file=disnake.File(fp=image_binary,
                                                     filename="image.png"))


def setup(bot):
    bot.add_cog(fun(bot))
