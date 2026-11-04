"""Regression: WoW Forever's ninth class, Horde Paladin (1.0.23)."""
import ast
import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BOT = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT / "corpsegrinder_wow_bot" / "community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(BOT)
STYLE_TREE = ast.parse(FEATURES)


def constant(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(name)


class FakeRole:
    def __init__(self, name, colour):
        self.name, self.colour = name, colour
        self.id = 999


class FakeGuild:
    def __init__(self, roles=()):
        self.roles = list(roles)
        self.creations = 0

    async def create_role(self, *, name, colour, reason):
        self.creations += 1
        obj = FakeRole(name, colour)
        self.roles.append(obj)
        return obj


class PaladinTests(unittest.TestCase):
    def test_nine_classes_include_horde_paladin(self):
        classes = constant(TREE, "CLASSES")
        self.assertEqual(len(classes), 9)
        self.assertIn("Paladin", classes)
        self.assertEqual(len(set(classes)), 9)
        self.assertIn("Paladin", constant(TREE, "EMOJI"))
        self.assertIn("Paladin", constant(STYLE_TREE, "ROLE_STYLE"))
        self.assertIn(" + CLASSES", BOT)
        self.assertIn('ToggleSelect(CLASSES,', BOT)
        self.assertIn('for klasse in CLASSES]', BOT)
        self.assertIn('for name in CLASSES]', BOT)
        self.assertIn('if klass not in CLASSES:', BOT)
        self.assertIn("neun Horde-Klassen", BOT)

    def test_paladin_role_added_once_and_existing_role_respected(self):
        node = next(x for x in TREE.body if isinstance(x, ast.AsyncFunctionDef)
                    and x.name == "ensure_paladin_role")
        fake_discord = SimpleNamespace(
            utils=SimpleNamespace(
                get=lambda members, name: next(
                    (role for role in members if role.name == name), None)),
            Colour=lambda colour: colour,
            HTTPException=RuntimeError)
        role_style = constant(STYLE_TREE, "ROLE_STYLE")
        env = {
            "discord": fake_discord,
            "ROLE_STYLE": role_style,
            "visual_name": lambda name: role_style[name][0],
            "logging": SimpleNamespace(
                info=lambda *args, **kwargs: None,
                exception=lambda *args, **kwargs: None),
        }
        def role(guild, name):
            return (fake_discord.utils.get(guild.roles, name=env["visual_name"](name))
                    or fake_discord.utils.get(guild.roles, name=name))
        env["role"] = role
        exec(compile(ast.fix_missing_locations(
            ast.Module(body=[node], type_ignores=[])), "bot.py", "exec"), env)
        guild = FakeGuild()
        created = asyncio.run(env["ensure_paladin_role"](guild))
        self.assertEqual(created.name, "🛡️ Paladin")
        self.assertEqual(guild.creations, 1)
        again = asyncio.run(env["ensure_paladin_role"](guild))
        self.assertIs(again, created)
        self.assertEqual(guild.creations, 1)
        old = FakeRole("Paladin", 0xABCDEF)
        guild2 = FakeGuild([old])
        self.assertIs(asyncio.run(env["ensure_paladin_role"](guild2)), old)
        self.assertEqual(guild2.creations, 0)

    def test_existing_profile_and_roles_not_deleted(self):
        self.assertIn("await ensure_paladin_role(guild)", BOT)
        self.assertIn('await publish_panel(guild)', BOT)
        self.assertIn("name=visual_name(\"Paladin\")", BOT)
        self.assertNotIn("DELETE FROM characters WHERE klass", BOT)


if __name__ == "__main__":
    unittest.main()
