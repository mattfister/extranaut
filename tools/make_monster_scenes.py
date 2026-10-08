"""Generate entities/monsters/*.tscn from the table below.

Static data for each monster kind lives here; behaviour lives in the script
each scene names. Re-running overwrites the scenes.

Usage: python tools/make_monster_scenes.py
"""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "entities" / "monsters"

TEMPLATE = """[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://entities/monsters/{script}.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/{texture}.png" id="2"]

[sub_resource type="PhysicsMaterial" id="material"]
friction = {friction}

[sub_resource type="CircleShape2D" id="shape"]
radius = {radius}

[node name="{node}" type="RigidBody2D"]
collision_layer = 4
collision_mask = 31
mass = {mass}
physics_material_override = SubResource("material")
gravity_scale = {gravity}
lock_rotation = {lock}
contact_monitor = true
max_contacts_reported = 8
script = ExtResource("1")
{exports}
[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("shape")

[node name="Sprite2D" type="Sprite2D" parent="."]
scale = Vector2(2, 2)
texture = ExtResource("2")
hframes = {hframes}
vframes = {vframes}
frame_coords = Vector2i({frame_x}, {frame_y})
"""


def monster(name, script, texture, frame=(0, 0), px=16, radius=16, mass=20,
            friction=0.5, gravity=1.0, lock=True, **exports):
    return dict(name=name, script=script, texture=texture, frame=frame, px=px,
                radius=radius, mass=mass, friction=friction, gravity=gravity,
                lock=lock, exports=exports)


HEAVY = dict(mass=40000, friction=40000)
DOOR = dict(px=32, radius=32, mass=20000, friction=100, damaged_by_shots=False, anim_frames=2)
BOSS = dict(px=32, radius=32, mass=200, damages_player_on_touch=True)
POWERUP = dict(is_powerup=True, damaged_by_shots=False, **HEAVY)
ALIEN = dict(death_sound="deadAlien")
BOT = dict(death_sound="explode", death_particles=40)
BIG = dict(death_sound="explode", death_particles=100)

MONSTERS = [
    monster("ball_monster", "ball_monster", "animations/ballMonster", lock=False, **ALIEN),
    monster("spiky_ball_monster", "ball_monster", "animations/ballMonster", frame=(0, 2),
            lock=False, damages_player_on_touch=True, **ALIEN),
    monster("jump_bot", "jump_bot", "animations/bots2", damages_player_on_touch=True, anim_frames=1, **BOT),
    monster("flyer", "flyer", "animations/ballMonster", frame=(0, 3), gravity=-1.0,
            damages_player_on_touch=True, **ALIEN),
    monster("fly_bot", "fly_bot", "animations/bots", gravity=-0.1, max_hp=3,
            damages_player_on_touch=True, **BOT),
    monster("boss_bot_1", "fly_bot", "animations/bossBots", gravity=-0.1, max_hp=6,
            damages_player_on_touch=True, drift_interval_max=0.075, drift_up_max=0.0, **BOT),
    monster("boss_bot_2", "fly_bot", "animations/bossBots", frame=(0, 1), gravity=-0.1, max_hp=6,
            damages_player_on_touch=True, first_fire_delay=1.0, fire_interval=0.5,
            random_spread=True, **BOT),
    monster("boss_bot_3", "fly_bot", "animations/bossBots", frame=(0, 2), gravity=-0.1, max_hp=10,
            damages_player_on_touch=True, **BOT),
    monster("aimer_turret", "aimer_turret", "animations/bots2", frame=(0, 2), mass=1000,
            gravity=-1.0, damages_player_on_touch=True, anim_frames=2, **BOT),
    monster("defense_turret_vertical", "defense_turret_vertical", "animations/turret", mass=5,
            gravity=0.8, death_sound="explode"),
    monster("hover_block", "hover_block", "sprites/chaosBlocks", frame=(1, 4), mass=4000,
            friction=20, gravity=0.0, anim_frames=1),
    monster("hand_bot", "hand_bot", "animations/bigBots1", px=32, radius=32, mass=200, max_hp=5,
            damages_player_on_touch=True, anim_frames=2, **BOT),
    monster("spiky_head_monster", "spiky_head_monster", "animations/snakeHeadBoss", frame=(0, 4),
            lock=False, damages_player_on_touch=True, damaged_by_shots=False, anim_frames=1,
            death_sound="explode"),
    monster("artifact_door", "artifact_door", "animations/artifactDoor", **DOOR),
    monster("monster_door", "monster_door", "animations/artifactDoor", frame=(0, 1), **DOOR),
    monster("monster_door_2", "monster_door", "animations/artifactDoor", frame=(0, 1),
            open_when_count=2, **DOOR),
    monster("save_point", "save_point", "animations/savePoint", is_save_point=True, **HEAVY),
    monster("hp_powerup", "powerup", "animations/collectibles", frame=(0, 2), kind="hp", **POWERUP),
    monster("fuel_powerup", "powerup", "animations/collectibles", kind="fuel", **POWERUP),
    monster("gun_powerup", "powerup", "animations/collectibles", frame=(0, 3), kind="gun", **POWERUP),
    monster("alien_artifact", "powerup", "animations/collectibles", frame=(0, 1), kind="artifact",
            **POWERUP),
    monster("orb_boss", "orb_boss", "animations/orbBoss", lock=False, max_hp=20, anim_frames=2,
            **BOSS, **BIG),
    monster("fallen_extranaut", "orb_boss", "animations/fallenExtranaut", lock=False, max_hp=20,
            grenade_offset=(32, 30), lob_grenades=False, fires_when_chasing=True,
            row_per_mode=False, **BOSS, **BIG),
    monster("octo_boss", "octo_boss", "animations/octoBoss", gravity=0.0, max_hp=20,
            anim_frames=1, **BOSS, **BIG),
    monster("head_boss", "head_boss", "animations/snakeHeadBoss", max_hp=15, anim_frames=1,
            death_sound="explode", death_particles=200, **BOSS),
]


def png_size(path):
    with open(path, "rb") as file:
        header = file.read(24)
    return struct.unpack(">II", header[16:24])


def godot_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"%s"' % value
    if isinstance(value, tuple):
        return "Vector2(%s, %s)" % value
    return repr(value)


def render(m):
    width, height = png_size(ROOT / "assets" / (m["texture"] + ".png"))
    exports = "".join("%s = %s\n" % (key, godot_value(value)) for key, value in m["exports"].items())
    return TEMPLATE.format(
        script=m["script"],
        texture=m["texture"],
        friction=float(m["friction"]),
        radius=float(m["radius"]),
        node="".join(part.capitalize() for part in m["name"].split("_")),
        mass=float(m["mass"]),
        gravity=float(m["gravity"]),
        lock=godot_value(m["lock"]),
        exports=exports,
        hframes=width // m["px"],
        vframes=height // m["px"],
        frame_x=m["frame"][0],
        frame_y=m["frame"][1],
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for m in MONSTERS:
        with open(OUT / (m["name"] + ".tscn"), "w", newline="\n") as file:
            file.write(render(m))
    print("Wrote %d monster scenes" % len(MONSTERS))


if __name__ == "__main__":
    main()
