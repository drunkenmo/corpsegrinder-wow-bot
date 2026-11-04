"""Corpsegrinder 1.0.19 regression: server layout and living welcome guide.

Runs without discord.py, Discord token or Home Assistant.
"""
import ast
import asyncio
import re
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
        self.assertIn('channel(member.guild, "lagerfeuer")',section)
        self.assertIn('channel(member.guild, "willkommen")',section)
        self.assertIn("welcome_link",section)
        self.assertIn("delete_after=24 * 3600",section)
        self.assertNotIn("Ingame-Name + Klasse",section)
        self.assertNotIn("Rollen wählen",section)
        self.assertNotIn('or channel(member.guild, "willkommen")',section)

    def test_new_member_gets_only_one_short_public_greeting(self):
        join_node=next(n for n in TREE.body
                       if isinstance(n,ast.AsyncFunctionDef)
                       and n.name=="on_member_join")
        join_node.decorator_list=[]  # Run isolated without a real Discord bot
        short_node=next(n for n in TREE.body
                        if isinstance(n,ast.FunctionDef)
                        and n.name=="short_lagerfeuer_greeting")

        class FakeTextChannel:
            def __init__(self,mention):
                self.mention=mention
                self.posts=[]
            async def send(self,content,**kwargs):
                self.posts.append((content,kwargs))

        class FakeMember:
            def __init__(self,guild):
                self.guild=guild
                self.mention="<@42>"
                self.roles=[]
            async def add_roles(self,role):
                self.roles.append(role)

        chat=FakeTextChannel("<#10>")
        welcome=FakeTextChannel("<#11>")
        community=object()
        guild=SimpleNamespace(id=12345)
        fake_discord=SimpleNamespace(
            TextChannel=FakeTextChannel,
            AllowedMentions=lambda **kwargs:SimpleNamespace(**kwargs),
            HTTPException=Exception,
            Forbidden=Exception)
        env={
            "discord":fake_discord,"GUILD_ID":12345,
            "role":lambda g,n: community if n=="Community" else None,
            "channel":lambda g,n:{"lagerfeuer":chat,
                                    "willkommen":welcome}.get(n),
            "logging":SimpleNamespace(warning=lambda *args:None)}
        exec(compile(ast.fix_missing_locations(
            ast.Module(body=[short_node,join_node],type_ignores=[])),
            "bot.py","exec"),env)
        member=FakeMember(guild)
        asyncio.run(env["on_member_join"](member))
        self.assertEqual(member.roles,[community])
        self.assertEqual(len(chat.posts),1)
        text,kwargs=chat.posts[0]
        self.assertIn("<@42>",text)
        self.assertIn("<#11>",text)
        self.assertNotIn("\\n",text)
        self.assertLess(len(text),120)
        self.assertEqual(kwargs["delete_after"],24*3600)
        self.assertTrue(kwargs["allowed_mentions"].users)
        self.assertFalse(kwargs["allowed_mentions"].everyone)
        self.assertEqual(welcome.posts,[])

        # Ausfall von #lagerfeuer darf #willkommen nicht vollschreiben.
        env["channel"]=lambda g,n:welcome if n=="willkommen" else None
        asyncio.run(env["on_member_join"](FakeMember(guild)))
        self.assertEqual(len(chat.posts),1)
        self.assertEqual(welcome.posts,[])


    def test_old_greetings_are_edited_in_place_exactly_once(self):
        """Only bot-authored legacy messages are edited; no chat is reposted."""
        selected=[n for n in TREE.body if (
            isinstance(n,ast.Assign) and any(
                isinstance(dst,ast.Name) and
                dst.id=="_OLD_LAGERFEUER_GREETING" for dst in n.targets))
            or (isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
                and n.name in ("short_lagerfeuer_greeting",
                               "compact_old_lagerfeuer_greetings"))]
        class FakeChat:
            def __init__(self,messages,mention):
                self.messages,self.mention=messages,mention
                self.send_count=0
                self.requested_history=False
            def history(self,limit):
                self.requested_history=True
                self.assert_limit=limit
                async def generator():
                    for m in self.messages:
                        yield m
                return generator()
            async def send(self,*args,**kwargs):
                self.send_count+=1
        class FakeMessage:
            def __init__(self,identifier,author_id,content):
                self.id=identifier
                self.author=SimpleNamespace(id=author_id)
                self.content=content
                self.edits=[]
                self.deletes=0
            async def edit(self,**kwargs):
                self.edits.append(kwargs)
                self.content=kwargs["content"]
            async def delete(self,*args,**kwargs):
                self.deletes+=1

        old_content=(
            "⚔️ Willkommen bei **Corpsegrinder**, <@42>! Für die Horde! 🍻\n"
            "Starte mit unserer Orientierung in <#11>. Danach in <#12> "
            "Rollen wählen und **Ingame-Name + Klasse** registrieren. "
            "Keine Freigabe erforderlich.")
        first=FakeMessage(100,999,old_content)
        second=FakeMessage(101,999,old_content.replace("<@42>","<@43>"))
        normal=FakeMessage(102,42,"Moin, spielt ihr heute?")
        other_bot=FakeMessage(103,111,old_content)
        modern=FakeMessage(104,999,"👋 Willkommen am Lagerfeuer, <@44>!")
        chat=FakeChat([first,second,normal,other_bot,modern],"<#10>")
        welcome=FakeChat([],"<#11>")
        storage={}
        class AllowedMentions:
            @staticmethod
            def none():
                return "no-pings"

        env={
            "re":re,
            "discord":SimpleNamespace(
                TextChannel=FakeChat,HTTPException=Exception,
                AllowedMentions=AllowedMentions),
            "channel":lambda guild,name:{
                "lagerfeuer":chat,"willkommen":welcome}.get(name),
            "bot":SimpleNamespace(user=SimpleNamespace(id=999)),
            "setting":lambda key:storage.get(key),
            "save_setting":lambda key,value:storage.__setitem__(key,value),
            "logging":SimpleNamespace(info=lambda *args:None,
                                      warning=lambda *args:None,
                                      exception=lambda *args:None)
        }
        exec(compile(ast.fix_missing_locations(
            ast.Module(body=selected,type_ignores=[])),
            "bot.py","exec"),env)
        asyncio.run(env["compact_old_lagerfeuer_greetings"](SimpleNamespace()))
        self.assertEqual(storage.get("lagerfeuer_greetings_compacted_v136"),"1")
        self.assertEqual(first.content,
                         "👋 Willkommen am Lagerfeuer, <@42>! 🍻 "
                         "Neu hier? Schau in <#11>.")
        self.assertEqual(len(first.edits),1)
        self.assertEqual(first.edits[0]["allowed_mentions"],"no-pings")
        self.assertEqual(len(second.edits),1)
        self.assertEqual(len(normal.edits),0)
        self.assertEqual(len(other_bot.edits),0)
        self.assertEqual(len(modern.edits),0)
        self.assertEqual(sum(m.deletes for m in chat.messages),0)
        self.assertEqual(chat.send_count,0)
        self.assertEqual(welcome.send_count,0)
        # Marker prevents touching old posts again on future bot restarts.
        asyncio.run(env["compact_old_lagerfeuer_greetings"](SimpleNamespace()))
        self.assertEqual(len(first.edits),1)
        self.assertEqual(len(second.edits),1)


if __name__=="__main__":
    unittest.main()
