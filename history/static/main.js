function demon_type(demon_type_number, rating_sum) {
    if (!demon_type_number && rating_sum != 30) return ""
    if (demon_type_number < 3 || rating_sum == 30) return "Hard"
    if (demon_type_number < 7) {
        type_list = ["Easy", "Medium", "Insane", "Extreme"]
        return type_list[demon_type_number - 3]
    }
    return `Hard (${demon_type_number})`
}

function difficulty(rating_sum, ratings, demon, auto, demon_type_number, game_version) {
    if (auto) return "Auto"
    if (demon) return `${demon_type(demon_type_number, rating_sum)} Demon`
    if (!ratings || !rating_sum || ratings < 5) return "N/A"

    const diffs = ["N/A", "Easy", "Normal", "Hard", "Harder", "Insane"]

    // prior to 1.5 difficulties were rounded incorrectly
    let diff = rating_sum / ratings
    if(game_version >= 6) diff = Math.round(diff)
    else diff = Math.floor(diff)

    if(diff >= diffs.length || diff < 0) return "N/A"
    return diffs[diff]
}

function display_number(number) {
    if (number == null) return "0"
    return number
}

function level_length(number) {
    const lengths = ["Tiny", "Short", "Medium", "Long", "XL", "Plat."]
    if(!number) number = 0
    if (number >= lengths.length || number < 0) return `Unknown (${number})`
    return lengths[number]
}

function epic_string(epic) {
    if (epic > 3) return `Mythic+ [${epic}]`
    if (epic == 3) return "Mythic"
    if (epic == 2) return "Legendary"
    if (epic == 1) return "Epic"
    if (epic < 1) return "Not Epic"
}

function print_featured(level) {
    if (level.feature_score > 0) {
        return `✅${level.epic ? ` (${epic_string(level.epic)})` : ""}`
    }
    return "❌"
}

function level_password(password) {
    if (!password) return "Not Copyable"
    if (password == 1) return "Free Copy"
    if (password >= 10000 && password <= 19999) return password % 10000
    if (password >= 1000000 && password <= 1999999) return password % 1000000
    return `Invalid (${password})`
}

function working_time(wt) {
    const seconds = wt % 60;
    const minutes = Math.floor(wt / 60) % 60;
    const hours = Math.floor(wt / 3600) % 24;
    const days = Math.floor(wt / 86400);

    let result = "";
    if (days > 0) result += `${days} day${days > 1 ? 's' : ''}, `;
    result += `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

    return result;
}

function approx_verification(timestamp) {
    return working_time(Math.round(timestamp / 240))
}

function star_character(length) {
    return length == 5 ? " ☾" : "*"
}

function difficulty_text(bestRecord) {
    return `${difficulty(bestRecord.rating_sum, bestRecord.rating, bestRecord.demon, bestRecord.auto, bestRecord.demon_type, bestRecord.game_version)} (${display_number(bestRecord.stars)}${star_character(bestRecord.length)})`
}

function epic_fires(epic, character) {
    return epic > 0 ? character.repeat(epic) : ""
}

function game_version(version) {
    if (!version) return ""
    if (version > 18) return (version / 10).toFixed(1)
    if (version == 18) return "1.81"
    if (version == 11) return "1.80"
    if (version == 10) return "1.7"
    return `1.${version - 1}`
}

function print_file_size(size) {
    if (size < 1024) return `${size} B`
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
    return `${(size / 1024 / 1024).toFixed(2)} MB`
}

function cached_username(cached_user) {
    return cached_user.non_player_username ? cached_user.non_player_username : cached_user.username
}

function record_date(date) {
    return new Date(date).toLocaleDateString("en-US", { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
}

function record_time(date) {
    let str = new Date(date).toLocaleTimeString("en-US", { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'UTC' })
    if(str == "12:00:00 AM") return ""
    return str
}

function official_song_name(id, gameVersion) {
    let PRACTICE = [
		"Stay Inside Me by OcularNebula"
	]
	let MAIN = [
		"Stereo Madness by ForeverBound", "Back on Track by DJVI", "Polargeist by Step", "Dry Out by DJVI", "Base after Base by DJVI",
		"Can't Let Go by DJVI", "Jumper by Waterflame", "Time Machine by Waterflame", "Cycles by DJVI", "xStep by DJVI",
		"Clutterfunk by Waterflame", "Theory of Everything by DJ Nate", "Electroman Adventures by Waterflame", "Clubstep by DJ Nate", "Electrodynamix by DJ Nate",
		"Hexagon Force by Waterflame", "Blast Processing by Waterflame", "Theory of Everything 2 by DJ Nate", "Geometrical Dominator by Waterflame", "Deadlocked by F-777",
		"Fingerdash by MDK", "Dash by MDK", "Explorers by Hinkik"
	]
    let ACTIVE = [
        "Active by DJVI"
    ]
	let MELTDOWN = [
		"The Seven Seas by F-777", "Viking Arena by F-777", "Airborne Robots by F-777"
	]
	let CHALLENGE = [
		"Secret (The Challenge)"
	]
	let WORLD = [
		"Payload by Dex Arson",
		"Beast Mode by Dex Arson",
		"Machina by Dex Arson",
		"Years by Dex Arson",
		"Frontlines by Dex Arson",
		"Space Pirates by Waterflame",
		"Striker by Waterflame",
		"Embers by Dex Arson",
		"Round 1 by Dex Arson",
		"Monster Dance Off by F-777"
	]
	let SUBZERO = [
		"Press Start by MDK",
		"Nock Em by Bossfight",
		"Power Trip by Boom Kitty"
	]

    let fullArray = [...PRACTICE, ...MAIN, ...MELTDOWN, ...CHALLENGE, ...WORLD, ...SUBZERO]

    if(gameVersion) {
        if(gameVersion <= 21) fullArray = [...fullArray.slice(0, 22), ...MELTDOWN, ...CHALLENGE, ...WORLD, ...SUBZERO]
        if(gameVersion <= 20) fullArray = [...fullArray.slice(0, 21), ...MELTDOWN]
        if(gameVersion <= 19) fullArray = [...fullArray.slice(0, 19), ...ACTIVE]
        if(gameVersion <= 18) fullArray = [...fullArray.slice(0, 17), ...ACTIVE]
        if(gameVersion <= 10) fullArray = [...fullArray.slice(0, 16), ...ACTIVE]
        if(gameVersion <= 7) fullArray = [...fullArray.slice(0, 15), ...ACTIVE]
        if(gameVersion <= 6) fullArray = [...fullArray.slice(0, 13), ...ACTIVE]
        if(gameVersion <= 5) fullArray = [...fullArray.slice(0, 12), ...ACTIVE]
    }

    return fullArray[id + 1] || "Unknown by DJVI"
    
}

function print_filter_difficulty(diff) {
    const values = ["Auto", "Easy", "Normal", "Hard", "Harder", "Insane", "Demon", "Easy Demon", "Medium Demon", "Hard Demon", "Insane Demon", "Extreme Demon"]
    if (diff > values.length || diff < -1) return "Unknown"
    if (diff <= 0) return "N/A"
    return values[diff - 1]
}

function escapeHtml(unsafe) {
    if (typeof unsafe !== "string") return unsafe
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}