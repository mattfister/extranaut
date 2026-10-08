extends Node
## Autoload "Audio": sound effects and crossfading music. Names are file
## names in assets/sounds without the extension.

const SOUND_PATH := "res://assets/sounds/%s.ogg"
const SFX_PLAYER_COUNT := 8
const SFX_VOLUME_DB := -6.0
const MUSIC_VOLUME_DB := -12.0
const SILENT_DB := -60.0
const FADE_TIME := 1.0
## The same effect is not restarted within this many milliseconds, so a burst
## of identical events is one sound.
const RETRIGGER_GAP_MS := 50

var _sfx_players: Array[AudioStreamPlayer] = []
## The effect last played on each player, in step with _sfx_players.
var _sfx_names: Array[String] = []
var _next_sfx := 0
var _last_played := {}
var _music_players: Array[AudioStreamPlayer] = []
var _active_music := 0
var _music_name := ""
var _fade: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in SFX_PLAYER_COUNT:
		var player := AudioStreamPlayer.new()
		player.volume_db = SFX_VOLUME_DB
		add_child(player)
		_sfx_players.append(player)
		_sfx_names.append("")
	for i in 2:
		var player := AudioStreamPlayer.new()
		player.volume_db = SILENT_DB
		add_child(player)
		_music_players.append(player)


func play(sound: String) -> void:
	var now := Time.get_ticks_msec()
	if _last_played.has(sound) and now - int(_last_played[sound]) < RETRIGGER_GAP_MS:
		return
	var stream := _load(sound)
	if stream == null:
		return
	_last_played[sound] = now
	var index := _pick_sfx_player()
	_sfx_names[index] = sound
	_sfx_players[index].stream = stream
	_sfx_players[index].play()


## Plays the effect unless it is already sounding. For continuous actions.
func play_if_idle(sound: String) -> void:
	if not is_playing(sound):
		play(sound)


func is_playing(sound: String) -> bool:
	return playing_count(sound) > 0


func playing_count(sound: String) -> int:
	var count := 0
	for i in SFX_PLAYER_COUNT:
		if _sfx_names[i] == sound and _sfx_players[i].playing:
			count += 1
	return count


## Crossfades to a looping track. Does nothing if it is already playing.
func play_music(track: String) -> void:
	if track == _music_name:
		return
	var stream := _load(track)
	if stream == null:
		return
	if stream is AudioStreamOggVorbis:
		stream.loop = true
	_music_name = track
	var old := _music_players[_active_music]
	_active_music = 1 - _active_music
	var fresh := _music_players[_active_music]
	fresh.stream = stream
	fresh.volume_db = SILENT_DB
	fresh.play()
	if _fade != null:
		_fade.kill()
	_fade = create_tween().set_parallel()
	_fade.tween_property(fresh, "volume_db", MUSIC_VOLUME_DB, FADE_TIME)
	_fade.tween_property(old, "volume_db", SILENT_DB, FADE_TIME)
	_fade.chain().tween_callback(old.stop)


func current_music() -> String:
	return _music_name


func music_player() -> AudioStreamPlayer:
	return _music_players[_active_music]


## A player that has finished, or failing that the least recently used.
func _pick_sfx_player() -> int:
	for i in SFX_PLAYER_COUNT:
		if not _sfx_players[i].playing:
			return i
	_next_sfx = (_next_sfx + 1) % SFX_PLAYER_COUNT
	return _next_sfx


func _load(sound: String) -> AudioStream:
	var path := SOUND_PATH % sound
	if not ResourceLoader.exists(path):
		push_warning("no sound named %s" % sound)
		return null
	return load(path)
