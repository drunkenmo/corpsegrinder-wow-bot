"""Corpsegrinder 1.0.19 regression: server layout and living welcome guide.

Runs without discord.py, Discord token or Home Assistant.
"""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
BOT=(ROOT/"corpsegrinder_wow_bot"/"bot.py").read_text(encoding="utf-8")
FEATURES=(ROOT/"corpsegrinder_wow_bot"/"community_features.py").read_text(encoding="utf-8")
TREE=ast.parse(BOT)
FEATURE_TREE=ast.parse(FEATURES)


def extract_constant(tree,name):
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for dest in node.targets:
                if isinstance(dest,ast.Name) and dest.id==name:
                    return ast.literal_eval(node.value)
    raise AssertionError("Missing constant "+name)


class FakeEmbed:
    def __init__(self,**kwargs):
        self.title=kwargs["title"]
        self.description=kwargs["description"]
        self.fields=[]
        self.footer=""
        self.image_url=""
    def add_field(self,*,name,value,inline):
        self.fields.append((name,value,inline))
    def set_image(self,*,url):
        self.image_url=url
    def set_footer(self,*,text):
        self.footer=text


def load_welcome():
    welcome=[item for item in FEATURE_TREE.body if isinstance(item,ast.FunctionDef)
             and item.name=="welcome_embed"]
    namespace={
        "discord":SimpleNamespace(
            Embed=FakeEmbed,
            Colour=SimpleNamespace(from_rgb=lambda *args:0),
            utils=SimpleNamespace(escape_markdown=lambda s:s.replace("*","\\*"))),
        "VERSION":extract_constant(FEATURE_TREE,"VERSION"),
        "WELCOME_FEATURES":extract_constant(FEATURE_TREE,"WELCOME_FEATURES")
    }
    compiled=compile(ast.fix_missing_locations(
        ast.Module(body=welcome,type_ignores=[])),"community_features.py","exec")
    exec(compiled,namespace)
    return namespace["welcome_embed"]


class LayoutAndGuideTests(unittest.TestCase):
    def test_start_category_is_welcome_then_roles(self):
        structure=extract_constant(TREE,"STRUCTURE")
        start=structure["🌋 WOW FOREVER | START"]
        self.assertEqual([name for name,_ in start],[
            "willkommen","rollenwahl","lagerfeuer",
            "ankündigungen","forever-news","addons"])
        self.assertEqual(list(structure)[1:],[
            "⚔️ WOW FOREVER | PVE",
            "🏹 WOW FOREVER | PVP",
            "🔨 WOW FOREVER | CHARAKTERE"])

    def test_welcome_contains_all_start_steps_and_function_directory(self):
        fn=load_welcome()
        guild=SimpleNamespace(text_channels=[
            SimpleNamespace(name=n,mention=f"<#{index}>")
            for index,n in enumerate([
                "rollenwahl","lagerfeuer","dungeon-planer","pve-gruppensuche",
                "pvp-gruppensuche","raids-und-termine","ankündigungen",
                "forever-news","addons","pve-guides","charaktere-und-berufe",
                "handel-und-crafting","screenshots"],100)])
        embed=fn(guild,"Sondertermin Samstag")
        self.assertIn("WILLKOMMEN",embed.title)
        self.assertIn("<#100>",embed.description)
        self.assertIn("Ingame-Namen + Klasse",embed.description)
        self.assertIn("corpsegrinder:welcome",embed.footer)
        self.assertIn("Version "+extract_constant(FEATURE_TREE,"VERSION"),embed.footer)
        self.assertIn("Sondertermin Samstag",str(embed.fields))
        for name in ("forever-news","addons","dungeon-planer","pve-gruppensuche"):
            self.assertIn(name,[chan for _sec,entries in extract_constant(
                FEATURE_TREE,"WELCOME_FEATURES") for chan,_txt in entries])
        self.assertLessEqual(len(embed.fields),25)
        self.assertTrue(all(len(value)<=1024 for _name,value,_ in embed.fields))

    def test_guide_can_render_without_guild(self):
        embed=load_welcome()()
        self.assertIn("#rollenwahl",embed.description)
        self.assertIn("#lagerfeuer",embed.description)

    def test_known_existing_welcome_post_is_updated_not_reposted(self):
        self.assertIn('welcome_embed(guild, setting("welcome_admin_tip") or "")',BOT)
        self.assertIn('target, "welcome_post", "corpsegrinder:welcome"',BOT)
        self.assertIn('await existing.edit(embed=embed, view=view)',BOT)
        self.assertIn('save_setting(storage_key, existing.id)',BOT)
        self.assertIn("await existing.pin(",BOT)

    def test_admin_can_refresh_and_post_custom_tip(self):
        self.assertIn('name="willkommen_aktualisieren"',BOT)
        self.assertIn('name="willkommenshinweis"',BOT)
        self.assertIn('save_setting("welcome_admin_tip",note)',BOT)
        self.assertIn('await organize_start_channels(i.guild)',BOT)
        self.assertIn('app_commands.Range[str,1,500]',BOT)
        self.assertIn('note="" if text.strip().casefold()',BOT)

    def test_news_worker_no_longer_reorders_every_poll(self):
        i=BOT.index("async def ensure_forever_news_channel")
        j=BOT.index("def forever_news_embed",i)
        self.assertIn("if created:",BOT[i:j])
        self.assertIn("await organize_start_channels(guild)",BOT[i:j])
        i=BOT.index("async def ensure_addons_channel")
        j=BOT.index("def addon_version_embed",i)
        self.assertIn("if created:",BOT[i:j])
        self.assertIn("await organize_start_channels(guild)",BOT[i:j])

    def test_user_greeting_keeps_welcome_as_reference_not_chat_spam(self):
        start=BOT.index("async def on_member_join(")
        finish=BOT.index("# Nur vom Bot erzeugte Sprachkanäle",start)
        section=BOT[start:finish]
        self.assertIn('channel(member.guild,"lagerfeuer")',section)
        self.assertIn('channel(member.guild,"willkommen")',section)
        self.assertIn("welcome_link",section)


if __name__=="__main__":
    unittest.main()
